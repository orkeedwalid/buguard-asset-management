from sqlalchemy import Column, String, DateTime, JSON, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
import enum
from app.database import Base

class AssetType(str, enum.Enum):
    domain = "domain"
    subdomain = "subdomain"
    ip_address = "ip_address"
    service = "service"
    certificate = "certificate"
    technology = "technology"

class AssetStatus(str, enum.Enum):
    active = "active"
    stale = "stale"
    archived = "archived"

def utcnow():
    return datetime.now(timezone.utc)

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True)
    api_key = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=utcnow)

    assets = relationship("Asset", back_populates="organization")

class Asset(Base):
    __tablename__ = "assets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    type = Column(Enum(AssetType), nullable=False)
    value = Column(String, nullable=False)
    status = Column(Enum(AssetStatus), default=AssetStatus.active)
    first_seen = Column(DateTime, default=utcnow)
    last_seen = Column(DateTime, default=utcnow, onupdate=utcnow)
    source = Column(String, default="import")
    tags = Column(JSON, default=list)
    metadata_ = Column("metadata", JSON, default=dict)

    organization = relationship("Organization", back_populates="assets")
    relationships_from = relationship(
        "AssetRelationship",
        foreign_keys="AssetRelationship.from_asset_id",
        back_populates="from_asset"
    )
    relationships_to = relationship(
        "AssetRelationship",
        foreign_keys="AssetRelationship.to_asset_id",
        back_populates="to_asset"
    )

class AssetRelationship(Base):
    __tablename__ = "asset_relationships"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    from_asset_id = Column(String, ForeignKey("assets.id"), nullable=False)
    to_asset_id = Column(String, ForeignKey("assets.id"), nullable=False)
    relationship_type = Column(String, nullable=False)
    created_at = Column(DateTime, default=utcnow)

    from_asset = relationship("Asset", foreign_keys=[from_asset_id], back_populates="relationships_from")
    to_asset = relationship("Asset", foreign_keys=[to_asset_id], back_populates="relationships_to")