from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID


class SkillManifest(BaseModel):
    name: str
    version: str
    description: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = []
    dependencies: Optional[Dict[str, str]] = {}
    runtime: Optional[str] = None
    entry_point: Optional[str] = None


class SkillBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    description: Optional[str] = None


class SkillCreate(SkillBase):
    manifest: Dict[str, Any]
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")


class SkillUpdate(BaseModel):
    description: Optional[str] = None
    readme: Optional[str] = None
    tags: Optional[str] = None


class SkillVersionCreate(BaseModel):
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")
    changelog: Optional[str] = None


class SkillVersionResponse(BaseModel):
    id: UUID
    version: str
    changelog: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class SkillResponse(SkillBase):
    id: UUID
    namespace_id: UUID
    version: str
    tags: str
    description: Optional[str] = None
    readme: Optional[str] = None
    download_count: int
    rating_avg: str
    rating_count: int
    status: str
    published_at: Optional[str] = None
    created_at: str
    namespace_slug: Optional[str] = None

    class Config:
        from_attributes = True


class SkillDetailResponse(SkillResponse):
    manifest: Dict[str, Any]
    versions: List[SkillVersionResponse] = []


class SkillRatingCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)


class SkillRatingResponse(BaseModel):
    id: UUID
    user_id: UUID
    skill_id: UUID
    rating: int
    created_at: str

    class Config:
        from_attributes = True
