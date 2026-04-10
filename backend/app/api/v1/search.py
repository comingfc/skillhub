from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from typing import List, Optional

from app.core.database import get_db
from app.models.user import Skill, Namespace
from app.schemas.skill import SkillResponse
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=List[SkillResponse])
async def search_skills(
    q: str = Query(..., min_length=1),
    namespace: Optional[str] = None,
    tags: Optional[str] = None,
    sort: str = "relevance",
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    # Build query
    query = select(Skill).where(Skill.status == "published")

    # Full-text search using ILIKE (simple approach, can be upgraded to PostgreSQL full-text)
    search_filter = or_(
        Skill.name.ilike(f"%{q}%"),
        Skill.description.ilike(f"%{q}%"),
    )
    query = query.where(search_filter)

    # Filter by namespace
    if namespace:
        ns_result = await db.execute(select(Namespace).where(Namespace.slug == namespace))
        ns = ns_result.scalar_one_or_none()
        if ns:
            query = query.where(Skill.namespace_id == ns.id)

    # Filter by tags
    if tags:
        query = query.where(Skill.tags == tags)

    # Sorting
    if sort == "downloads":
        query = query.order_by(Skill.download_count.desc())
    elif sort == "rating":
        query = query.order_by(Skill.rating_avg.desc())
    elif sort == "recent":
        query = query.order_by(Skill.published_at.desc())
    else:  # relevance - just use existing filter order
        query = query.order_by(Skill.download_count.desc())

    # Pagination
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    skills = result.scalars().all()

    # Get namespace slugs
    responses = []
    for skill in skills:
        ns_result = await db.execute(select(Namespace).where(Namespace.id == skill.namespace_id))
        ns = ns_result.scalar_one_or_none()
        responses.append({
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
            "namespace_slug": ns.slug if ns else None,
        })

    return responses
