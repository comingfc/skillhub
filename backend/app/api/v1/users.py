from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid

from app.core.database import get_db
from app.models.user import User, Skill, SkillFavorite
from app.schemas.user import UserResponse, UserUpdate
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == uuid.UUID(current_user["id"])))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return {
        "id": str(user.id),
        "email": user.email,
        "username": user.username,
        "avatar_url": user.avatar_url,
        "bio": user.bio,
        "is_platform_admin": user.is_platform_admin,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    data: UserUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == uuid.UUID(current_user["id"])))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if data.avatar_url is not None:
        user.avatar_url = data.avatar_url
    if data.bio is not None:
        user.bio = data.bio

    await db.commit()
    await db.refresh(user)

    return {
        "id": str(user.id),
        "email": user.email,
        "username": user.username,
        "avatar_url": user.avatar_url,
        "bio": user.bio,
        "is_platform_admin": user.is_platform_admin,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@router.get("/me/favorites", response_model=List[dict])
async def get_user_favorites(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SkillFavorite, Skill)
        .join(Skill, SkillFavorite.skill_id == Skill.id)
        .where(SkillFavorite.user_id == uuid.UUID(current_user["id"]))
        .order_by(SkillFavorite.created_at.desc())
    )
    favorites = result.all()

    return [
        {
            "id": str(fav.skill_id),
            "name": skill.name,
            "slug": skill.slug,
            "namespace_id": str(skill.namespace_id),
            "version": skill.version,
            "tags": skill.tags,
            "description": skill.description,
            "rating_avg": skill.rating_avg,
            "download_count": skill.download_count,
            "favorited_at": fav.created_at.isoformat() if fav.created_at else None,
        }
        for fav, skill in favorites
    ]
