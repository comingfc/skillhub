from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid
import re

from app.core.database import get_db
from app.models.user import Namespace, NamespaceMember, User, AuditLog, NamespaceRole
from app.schemas.namespace import (
    NamespaceCreate,
    NamespaceUpdate,
    NamespaceResponse,
    NamespaceMemberResponse,
    NamespaceMemberUpdate,
)
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/namespaces", tags=["namespaces"])


def to_response(ns: Namespace) -> dict:
    return {
        "id": str(ns.id),
        "name": ns.name,
        "slug": ns.slug,
        "description": ns.description,
        "visibility": ns.visibility,
        "owner_id": str(ns.owner_id),
        "settings": ns.settings or {},
        "created_at": ns.created_at.isoformat() if ns.created_at else None,
        "updated_at": ns.updated_at.isoformat() if ns.updated_at else None,
    }


@router.get("", response_model=List[NamespaceResponse])
async def list_namespaces(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(Namespace)
        .where(
            (Namespace.visibility == "public")
            | (Namespace.owner_id == uuid.UUID(current_user["id"]))
            | (
                Namespace.id.in_(
                    select(NamespaceMember.namespace_id).where(
                        NamespaceMember.user_id == uuid.UUID(current_user["id"])
                    )
                )
            )
        )
        .order_by(Namespace.created_at.desc())
    )
    namespaces = result.scalars().all()
    return [to_response(ns) for ns in namespaces]


@router.post("", response_model=NamespaceResponse)
async def create_namespace(
    data: NamespaceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    # Validate slug format
    if not re.match(r"^[a-z0-9-]+$", data.slug):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slug must contain only lowercase letters, numbers, and hyphens",
        )

    # Check if slug exists
    result = await db.execute(select(Namespace).where(Namespace.slug == data.slug))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slug already taken",
        )

    namespace = Namespace(
        name=data.name,
        slug=data.slug,
        description=data.description,
        visibility=data.visibility,
        owner_id=uuid.UUID(current_user["id"]),
    )
    db.add(namespace)

    # Add owner as admin member
    member = NamespaceMember(
        namespace_id=namespace.id,
        user_id=uuid.UUID(current_user["id"]),
        role=NamespaceRole.ADMIN.value,
    )
    db.add(member)

    # Audit log
    audit = AuditLog(
        user_id=uuid.UUID(current_user["id"]),
        action="create",
        resource_type="namespace",
        resource_id=data.slug,
        metadata={"name": data.name},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(namespace)

    return to_response(namespace)


@router.get("/{slug}", response_model=NamespaceResponse)
async def get_namespace(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(Namespace).where(Namespace.slug == slug))
    namespace = result.scalar_one_or_none()

    if not namespace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Namespace not found",
        )

    # Check access
    if namespace.visibility != "public" and namespace.owner_id != uuid.UUID(current_user["id"]):
        # Check membership
        member_result = await db.execute(
            select(NamespaceMember).where(
                NamespaceMember.namespace_id == namespace.id,
                NamespaceMember.user_id == uuid.UUID(current_user["id"]),
            )
        )
        if not member_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

    return to_response(namespace)


@router.put("/{slug}", response_model=NamespaceResponse)
async def update_namespace(
    slug: str,
    data: NamespaceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(Namespace).where(Namespace.slug == slug))
    namespace = result.scalar_one_or_none()

    if not namespace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Namespace not found",
        )

    # Check permission (owner or admin)
    if not await _is_admin(namespace.id, current_user["id"], db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    if data.name is not None:
        namespace.name = data.name
    if data.description is not None:
        namespace.description = data.description
    if data.visibility is not None:
        namespace.visibility = data.visibility
    if data.settings is not None:
        namespace.settings = data.settings

    await db.commit()
    await db.refresh(namespace)

    return to_response(namespace)


@router.delete("/{slug}")
async def delete_namespace(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(Namespace).where(Namespace.slug == slug))
    namespace = result.scalar_one_or_none()

    if not namespace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Namespace not found",
        )

    if namespace.owner_id != uuid.UUID(current_user["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owner can delete namespace",
        )

    await db.delete(namespace)
    await db.commit()

    return {"message": "Namespace deleted"}


@router.get("/{slug}/members", response_model=List[NamespaceMemberResponse])
async def list_members(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(Namespace).where(Namespace.slug == slug))
    namespace = result.scalar_one_or_none()

    if not namespace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Namespace not found",
        )

    result = await db.execute(
        select(NamespaceMember, User)
        .join(User, NamespaceMember.user_id == User.id)
        .where(NamespaceMember.namespace_id == namespace.id)
    )
    members = result.all()

    return [
        {
            "id": str(member.id),
            "user_id": str(member.user_id),
            "role": member.role,
            "joined_at": member.joined_at.isoformat() if member.joined_at else None,
            "username": user.username,
            "email": user.email,
        }
        for member, user in members
    ]


@router.post("/{slug}/members")
async def add_member(
    slug: str,
    user_id: str,
    role: str = "member",
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(Namespace).where(Namespace.slug == slug))
    namespace = result.scalar_one_or_none()

    if not namespace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Namespace not found",
        )

    if not await _is_admin(namespace.id, current_user["id"], db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    # Check if user exists
    user_result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check if already a member
    result = await db.execute(
        select(NamespaceMember).where(
            NamespaceMember.namespace_id == namespace.id,
            NamespaceMember.user_id == uuid.UUID(user_id),
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member",
        )

    member = NamespaceMember(
        namespace_id=namespace.id,
        user_id=uuid.UUID(user_id),
        role=role,
        invited_by=uuid.UUID(current_user["id"]),
    )
    db.add(member)

    audit = AuditLog(
        user_id=uuid.UUID(current_user["id"]),
        action="invite",
        resource_type="namespace_member",
        resource_id=str(namespace.id),
        metadata={"added_user_id": user_id, "role": role},
    )
    db.add(audit)

    await db.commit()

    return {"message": "Member added"}


@router.put("/{slug}/members/{member_user_id}")
async def update_member(
    slug: str,
    member_user_id: str,
    data: NamespaceMemberUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(Namespace).where(Namespace.slug == slug))
    namespace = result.scalar_one_or_none()

    if not namespace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Namespace not found",
        )

    if not await _is_admin(namespace.id, current_user["id"], db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    result = await db.execute(
        select(NamespaceMember).where(
            NamespaceMember.namespace_id == namespace.id,
            NamespaceMember.user_id == uuid.UUID(member_user_id),
        )
    )
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )

    member.role = data.role

    audit = AuditLog(
        user_id=uuid.UUID(current_user["id"]),
        action="change_role",
        resource_type="namespace_member",
        resource_id=str(namespace.id),
        metadata={"affected_user_id": member_user_id, "new_role": data.role},
    )
    db.add(audit)

    await db.commit()

    return {"message": "Member updated"}


@router.delete("/{slug}/members/{member_user_id}")
async def remove_member(
    slug: str,
    member_user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(Namespace).where(Namespace.slug == slug))
    namespace = result.scalar_one_or_none()

    if not namespace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Namespace not found",
        )

    if not await _is_admin(namespace.id, current_user["id"], db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    result = await db.execute(
        select(NamespaceMember).where(
            NamespaceMember.namespace_id == namespace.id,
            NamespaceMember.user_id == uuid.UUID(member_user_id),
        )
    )
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )

    await db.delete(member)

    audit = AuditLog(
        user_id=uuid.UUID(current_user["id"]),
        action="remove_member",
        resource_type="namespace_member",
        resource_id=str(namespace.id),
        metadata={"removed_user_id": member_user_id},
    )
    db.add(audit)

    await db.commit()

    return {"message": "Member removed"}


async def _is_admin(namespace_id: uuid.UUID, user_id: str, db: AsyncSession) -> bool:
    # Owner is always admin
    result = await db.execute(
        select(Namespace).where(
            Namespace.id == namespace_id,
            Namespace.owner_id == uuid.UUID(user_id),
        )
    )
    if result.scalar_one_or_none():
        return True

    # Check admin role
    result = await db.execute(
        select(NamespaceMember).where(
            NamespaceMember.namespace_id == namespace_id,
            NamespaceMember.user_id == uuid.UUID(user_id),
            NamespaceMember.role.in_(["admin", "owner"]),
        )
    )
    return result.scalar_one_or_none() is not None
