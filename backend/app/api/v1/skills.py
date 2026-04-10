from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from typing import List, Optional
import uuid
import os
import tempfile
import zipfile
import boto3
from botocore.exceptions import ClientError

from app.core.database import get_db
from app.core.config import settings
from app.models.user import Skill, SkillVersion, SkillRating, SkillFavorite, Namespace, NamespaceMember, AuditLog, SkillStatus, SkillTag
from app.schemas.skill import (
    SkillCreate,
    SkillUpdate,
    SkillResponse,
    SkillDetailResponse,
    SkillVersionCreate,
    SkillVersionResponse,
    SkillRatingCreate,
)
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/skills", tags=["skills"])


def to_skill_response(skill: Skill, namespace_slug: str = None) -> dict:
    return {
        "id": str(skill.id),
        "namespace_id": str(skill.namespace_id),
        "name": skill.name,
        "slug": skill.slug,
        "version": skill.version,
        "tags": skill.tags,
        "description": skill.description,
        "readme": skill.readme,
        "download_count": skill.download_count,
        "rating_avg": skill.rating_avg,
        "rating_count": skill.rating_count,
        "status": skill.status,
        "published_at": skill.published_at.isoformat() if skill.published_at else None,
        "created_at": skill.created_at.isoformat() if skill.created_at else None,
        "namespace_slug": namespace_slug,
    }


@router.get("", response_model=List[SkillResponse])
async def list_skills(
    namespace: Optional[str] = None,
    tags: Optional[str] = None,
    status: Optional[str] = "published",
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    query = select(Skill).where(Skill.status == (status or SkillStatus.PUBLISHED.value))

    if namespace:
        # Get namespace by slug
        ns_result = await db.execute(select(Namespace).where(Namespace.slug == namespace))
        ns = ns_result.scalar_one_or_none()
        if ns:
            query = query.where(Skill.namespace_id == ns.id)

    if tags:
        query = query.where(Skill.tags == tags)

    query = query.order_by(Skill.download_count.desc(), Skill.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    skills = result.scalars().all()

    # Get namespace slugs
    responses = []
    for skill in skills:
        ns_result = await db.execute(select(Namespace).where(Namespace.id == skill.namespace_id))
        ns = ns_result.scalar_one_or_none()
        responses.append(to_skill_response(skill, ns.slug if ns else None))

    return responses


@router.post("", response_model=SkillResponse)
async def create_skill(
    name: str = Form(...),
    slug: str = Form(...),
    version: str = Form(...),
    manifest: str = Form(...),  # JSON string
    description: Optional[str] = Form(None),
    tags: str = Form("beta"),
    namespace_slug: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    import json

    # Validate namespace
    ns_result = await db.execute(select(Namespace).where(Namespace.slug == namespace_slug))
    ns = ns_result.scalar_one_or_none()
    if not ns:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Namespace not found")

    # Check permission
    if not await _can_publish(ns.id, current_user["id"], db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No publish permission")

    # Check if skill slug exists in namespace
    result = await db.execute(
        select(Skill).where(
            Skill.namespace_id == ns.id,
            Skill.slug == slug,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Skill slug already exists in namespace")

    # Validate manifest
    try:
        manifest_data = json.loads(manifest)
    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid manifest JSON")

    # Upload to S3
    zip_path = await _upload_to_s3(file, namespace_slug, slug, version)

    skill = Skill(
        namespace_id=ns.id,
        name=name,
        slug=slug,
        version=version,
        tags=tags,
        description=description,
        manifest=manifest_data,
        status=SkillStatus.PUBLISHED.value,
        published_at=datetime.utcnow(),
    )
    db.add(skill)
    await db.flush()

    skill_version = SkillVersion(
        skill_id=skill.id,
        version=version,
        manifest=manifest_data,
        zip_path=zip_path,
    )
    db.add(skill_version)

    audit = AuditLog(
        user_id=uuid.UUID(current_user["id"]),
        action="publish",
        resource_type="skill",
        resource_id=f"{namespace_slug}:{slug}",
        extra_data={"version": version},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(skill)

    return to_skill_response(skill, namespace_slug)


@router.get("/{namespace}:{slug}", response_model=SkillDetailResponse)
async def get_skill(
    namespace: str,
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ns_result = await db.execute(select(Namespace).where(Namespace.slug == namespace))
    ns = ns_result.scalar_one_or_none()
    if not ns:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Namespace not found")

    result = await db.execute(
        select(Skill).where(
            Skill.namespace_id == ns.id,
            Skill.slug == slug,
        )
    )
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")

    # Get versions
    versions_result = await db.execute(
        select(SkillVersion)
        .where(SkillVersion.skill_id == skill.id)
        .order_by(SkillVersion.created_at.desc())
    )
    versions = versions_result.scalars().all()

    return {
        **to_skill_response(skill, namespace),
        "manifest": skill.manifest,
        "versions": [
            {
                "id": str(v.id),
                "version": v.version,
                "changelog": v.changelog,
                "created_at": v.created_at.isoformat() if v.created_at else None,
            }
            for v in versions
        ],
    }


@router.post("/{namespace}:{slug}/versions", response_model=SkillVersionResponse)
async def create_skill_version(
    namespace: str,
    slug: str,
    data: SkillVersionCreate,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ns_result = await db.execute(select(Namespace).where(Namespace.slug == namespace))
    ns = ns_result.scalar_one_or_none()
    if not ns:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Namespace not found")

    result = await db.execute(
        select(Skill).where(
            Skill.namespace_id == ns.id,
            Skill.slug == slug,
        )
    )
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")

    if not await _can_publish(ns.id, current_user["id"], db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No publish permission")

    # Check version doesn't exist
    result = await db.execute(
        select(SkillVersion).where(
            SkillVersion.skill_id == skill.id,
            SkillVersion.version == data.version,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Version already exists")

    # Upload to S3
    zip_path = await _upload_to_s3(file, namespace, slug, data.version)

    skill_version = SkillVersion(
        skill_id=skill.id,
        version=data.version,
        manifest=skill.manifest,
        zip_path=zip_path,
        changelog=data.changelog,
    )
    db.add(skill_version)

    # Update skill version and set as latest
    skill.version = data.version
    skill.tags = SkillTag.LATEST.value
    skill.published_at = datetime.utcnow()

    audit = AuditLog(
        user_id=uuid.UUID(current_user["id"]),
        action="publish",
        resource_type="skill_version",
        resource_id=f"{namespace}:{slug}",
        extra_data={"version": data.version},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(skill_version)

    return {
        "id": str(skill_version.id),
        "version": skill_version.version,
        "changelog": skill_version.changelog,
        "created_at": skill_version.created_at.isoformat() if skill_version.created_at else None,
    }


@router.get("/{namespace}:{slug}/download")
async def download_skill(
    namespace: str,
    slug: str,
    version: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ns_result = await db.execute(select(Namespace).where(Namespace.slug == namespace))
    ns = ns_result.scalar_one_or_none()
    if not ns:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Namespace not found")

    result = await db.execute(
        select(Skill).where(
            Skill.namespace_id == ns.id,
            Skill.slug == slug,
        )
    )
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")

    if version:
        sv_result = await db.execute(
            select(SkillVersion).where(
                SkillVersion.skill_id == skill.id,
                SkillVersion.version == version,
            )
        )
    else:
        sv_result = await db.execute(
            select(SkillVersion).where(SkillVersion.skill_id == skill.id)
            .order_by(SkillVersion.created_at.desc())
            .limit(1)
        )

    skill_version = sv_result.scalar_one_or_none()
    if not skill_version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")

    # Increment download count
    skill.download_count += 1
    await db.commit()

    # Generate presigned URL
    s3_client = boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
    )

    try:
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.S3_BUCKET, "Key": skill_version.zip_path},
            ExpiresIn=3600,
        )
        return {"url": url}
    except ClientError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate download URL")


@router.post("/{namespace}:{slug}/rate")
async def rate_skill(
    namespace: str,
    slug: str,
    data: SkillRatingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ns_result = await db.execute(select(Namespace).where(Namespace.slug == namespace))
    ns = ns_result.scalar_one_or_none()
    if not ns:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Namespace not found")

    result = await db.execute(
        select(Skill).where(
            Skill.namespace_id == ns.id,
            Skill.slug == slug,
        )
    )
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")

    user_id = uuid.UUID(current_user["id"])

    # Check existing rating
    result = await db.execute(
        select(SkillRating).where(
            SkillRating.skill_id == skill.id,
            SkillRating.user_id == user_id,
        )
    )
    existing_rating = result.scalar_one_or_none()

    if existing_rating:
        existing_rating.rating = data.rating
    else:
        rating = SkillRating(
            user_id=user_id,
            skill_id=skill.id,
            rating=data.rating,
        )
        db.add(rating)

    # Recalculate average
    result = await db.execute(
        select(func.avg(SkillRating.rating), func.count(SkillRating.id))
        .where(SkillRating.skill_id == skill.id)
    )
    avg, count = result.one()
    skill.rating_avg = f"{avg:.1f}" if avg else "0.0"
    skill.rating_count = count or 0

    audit = AuditLog(
        user_id=user_id,
        action="rate",
        resource_type="skill",
        resource_id=f"{namespace}:{slug}",
        extra_data={"rating": data.rating},
    )
    db.add(audit)

    await db.commit()

    return {"message": "Rating saved", "rating_avg": skill.rating_avg, "rating_count": skill.rating_count}


@router.post("/{namespace}:{slug}/favorite")
async def favorite_skill(
    namespace: str,
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ns_result = await db.execute(select(Namespace).where(Namespace.slug == namespace))
    ns = ns_result.scalar_one_or_none()
    if not ns:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Namespace not found")

    result = await db.execute(
        select(Skill).where(
            Skill.namespace_id == ns.id,
            Skill.slug == slug,
        )
    )
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")

    user_id = uuid.UUID(current_user["id"])

    # Check existing
    result = await db.execute(
        select(SkillFavorite).where(
            SkillFavorite.skill_id == skill.id,
            SkillFavorite.user_id == user_id,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already favorited")

    favorite = SkillFavorite(user_id=user_id, skill_id=skill.id)
    db.add(favorite)

    audit = AuditLog(
        user_id=user_id,
        action="favorite",
        resource_type="skill",
        resource_id=f"{namespace}:{slug}",
    )
    db.add(audit)

    await db.commit()

    return {"message": "Added to favorites"}


@router.delete("/{namespace}:{slug}/favorite")
async def unfavorite_skill(
    namespace: str,
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ns_result = await db.execute(select(Namespace).where(Namespace.slug == namespace))
    ns = ns_result.scalar_one_or_none()
    if not ns:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Namespace not found")

    result = await db.execute(
        select(Skill).where(
            Skill.namespace_id == ns.id,
            Skill.slug == slug,
        )
    )
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")

    user_id = uuid.UUID(current_user["id"])

    result = await db.execute(
        select(SkillFavorite).where(
            SkillFavorite.skill_id == skill.id,
            SkillFavorite.user_id == user_id,
        )
    )
    favorite = result.scalar_one_or_none()
    if not favorite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not favorited")

    await db.delete(favorite)

    audit = AuditLog(
        user_id=user_id,
        action="unfavorite",
        resource_type="skill",
        resource_id=f"{namespace}:{slug}",
    )
    db.add(audit)

    await db.commit()

    return {"message": "Removed from favorites"}


async def _can_publish(namespace_id: uuid.UUID, user_id: str, db: AsyncSession) -> bool:
    # Owner can always publish
    result = await db.execute(
        select(Namespace).where(
            Namespace.id == namespace_id,
            Namespace.owner_id == uuid.UUID(user_id),
        )
    )
    if result.scalar_one_or_none():
        return True

    # Admin or member can publish (based on namespace settings)
    result = await db.execute(
        select(NamespaceMember).where(
            NamespaceMember.namespace_id == namespace_id,
            NamespaceMember.user_id == uuid.UUID(user_id),
        )
    )
    return result.scalar_one_or_none() is not None


async def _upload_to_s3(file: UploadFile, namespace: str, slug: str, version: str) -> str:
    import json

    # Create temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    s3_client = boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
    )

    key = f"skills/{namespace}/{slug}/{version}.zip"

    try:
        s3_client.upload_file(tmp_path, settings.S3_BUCKET, key)
    finally:
        os.unlink(tmp_path)

    return key


from datetime import datetime
