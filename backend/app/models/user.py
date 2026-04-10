import uuid
from datetime import datetime
import enum

from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Integer, Index
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    is_platform_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owned_namespaces = relationship("Namespace", back_populates="owner")
    memberships = relationship("NamespaceMember", back_populates="user")
    api_tokens = relationship("APIToken", back_populates="user")
    ratings = relationship("SkillRating", back_populates="user")
    favorites = relationship("SkillFavorite", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")


class NamespaceVisibility(str, enum.Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    TEAM = "team"


class NamespaceRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class Namespace(Base):
    __tablename__ = "namespaces"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    visibility = Column(String(50), default=NamespaceVisibility.PRIVATE.value)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    settings = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="owned_namespaces")
    members = relationship("NamespaceMember", back_populates="namespace", cascade="all, delete-orphan")
    skills = relationship("Skill", back_populates="namespace", cascade="all, delete-orphan")


class NamespaceMember(Base):
    __tablename__ = "namespace_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    namespace_id = Column(UUID(as_uuid=True), ForeignKey("namespaces.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role = Column(String(50), default="member")
    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    joined_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    namespace = relationship("Namespace", back_populates="members")
    user = relationship("User", foreign_keys=[user_id], back_populates="memberships")
    inviter = relationship("User", foreign_keys=[invited_by])


class SkillStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class SkillTag(str, enum.Enum):
    BETA = "beta"
    STABLE = "stable"
    LATEST = "latest"


class Skill(Base):
    __tablename__ = "skills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    namespace_id = Column(UUID(as_uuid=True), ForeignKey("namespaces.id"), nullable=False)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False)
    version = Column(String(50), nullable=False)
    tags = Column(String(50), default=SkillTag.BETA.value)
    description = Column(Text, nullable=True)
    readme = Column(Text, nullable=True)
    manifest = Column(JSON, nullable=False)
    download_count = Column(Integer, default=0)
    rating_avg = Column(String(10), default="0.0")
    rating_count = Column(Integer, default=0)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String(50), default=SkillStatus.DRAFT.value)

    # Unique constraint for namespace + slug
    __table_args__ = (
        Index('ix_skills_namespace_slug', 'namespace_id', 'slug', unique=True),
    )

    # Relationships
    namespace = relationship("Namespace", back_populates="skills")
    versions = relationship("SkillVersion", back_populates="skill", cascade="all, delete-orphan")
    ratings = relationship("SkillRating", back_populates="skill", cascade="all, delete-orphan")
    favorites = relationship("SkillFavorite", back_populates="skill", cascade="all, delete-orphan")


class SkillVersion(Base):
    __tablename__ = "skill_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("skills.id"), nullable=False)
    version = Column(String(50), nullable=False)
    manifest = Column(JSON, nullable=False)
    zip_path = Column(String(500), nullable=False)
    changelog = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    skill = relationship("Skill", back_populates="versions")

    __table_args__ = (
        Index('ix_skill_versions_skill_version', 'skill_id', 'version', unique=True),
    )


class SkillRating(Base):
    __tablename__ = "skill_ratings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("skills.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="ratings")
    skill = relationship("Skill", back_populates="ratings")

    __table_args__ = (
        Index('ix_skill_ratings_user_skill', 'user_id', 'skill_id', unique=True),
    )


class SkillFavorite(Base):
    __tablename__ = "skill_favorites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("skills.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="favorites")
    skill = relationship("Skill", back_populates="favorites")

    __table_args__ = (
        Index('ix_skill_favorites_user_skill', 'user_id', 'skill_id', unique=True),
    )


class AuditAction(str, enum.Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    PUBLISH = "publish"
    ARCHIVE = "archive"
    RATE = "rate"
    FAVORITE = "favorite"
    UNFAVORITE = "unfavorite"
    INVITE = "invite"
    REMOVE_MEMBER = "remove_member"
    CHANGE_ROLE = "change_role"
    PROMOTE = "promote"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action = Column(String(50), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(100), nullable=True)
    metadata = Column(JSON, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="audit_logs")


class APIToken(Base):
    __tablename__ = "api_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    token_hash = Column(String(255), nullable=False)
    expires_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="api_tokens")
