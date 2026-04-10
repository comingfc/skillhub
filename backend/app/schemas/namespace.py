from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID


class NamespaceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    description: Optional[str] = None
    visibility: str = "private"


class NamespaceCreate(NamespaceBase):
    pass


class NamespaceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    visibility: Optional[str] = None
    settings: Optional[dict] = None


class NamespaceResponse(NamespaceBase):
    id: UUID
    owner_id: UUID
    created_at: str

    class Config:
        from_attributes = True


class NamespaceMemberResponse(BaseModel):
    id: UUID
    user_id: UUID
    role: str
    joined_at: str
    username: Optional[str] = None
    email: Optional[str] = None

    class Config:
        from_attributes = True


class NamespaceMemberUpdate(BaseModel):
    role: str = Field(..., pattern=r"^(admin|member)$")
