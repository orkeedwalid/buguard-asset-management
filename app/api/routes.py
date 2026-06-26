from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Asset, AssetRelationship, AssetStatus, Organization
from app.schemas import AssetCreate, AssetResponse, BulkImportRequest
from app.auth import verify_api_key
from datetime import datetime, timezone
from typing import List, Optional
import uuid

router = APIRouter()

def utcnow():
    return datetime.now(timezone.utc)

# ─── Organization management ──────────────────────────────────────────────────

@router.post("/organizations")
def create_organization(name: str, db: Session = Depends(get_db)):
    existing = db.query(Organization).filter(Organization.name == name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Organization already exists")

    org = Organization(
        id=str(uuid.uuid4()),
        name=name,
        api_key=f"bg-{uuid.uuid4().hex}"
    )
    db.add(org)
    db.commit()
    return {
        "id": org.id,
        "name": org.name,
        "api_key": org.api_key,
        "message": "Save this API key — it won't be shown again"
    }

@router.get("/organizations/me")
def get_my_org(org: Organization = Depends(verify_api_key)):
    return {
        "id": org.id,
        "name": org.name,
        "created_at": org.created_at
    }

# ─── Asset endpoints ──────────────────────────────────────────────────────────

@router.post("/import")
def bulk_import(
    request: BulkImportRequest,
    db: Session = Depends(get_db),
    org: Organization = Depends(verify_api_key)
):
    imported = 0
    updated = 0
    failed = 0
    errors = []

    for item in request.assets:
        try:
            if not item.value or not item.type:
                failed += 1
                errors.append(f"Missing required fields for asset: {item}")
                continue

            existing = db.query(Asset).filter(
                Asset.value == item.value,
                Asset.type == item.type,
                Asset.org_id == org.id
            ).first()

            if existing:
                existing.last_seen = utcnow()
                existing.tags = list(set((existing.tags or []) + (item.tags or [])))
                existing.metadata_ = {**(existing.metadata_ or {}), **(item.metadata or {})}
                if existing.status == AssetStatus.stale:
                    existing.status = AssetStatus.active
                updated += 1
            else:
                asset = Asset(
                    id=item.id or str(uuid.uuid4()),
                    org_id=org.id,
                    type=item.type,
                    value=item.value,
                    status=item.status or AssetStatus.active,
                    source=item.source or "import",
                    tags=item.tags or [],
                    metadata_=item.metadata or {},
                    first_seen=utcnow(),
                    last_seen=utcnow(),
                )
                db.add(asset)
                imported += 1

        except Exception as e:
            failed += 1
            errors.append(str(e))

    db.commit()
    return {
        "imported": imported,
        "updated": updated,
        "failed": failed,
        "errors": errors
    }


@router.get("/assets", response_model=List[AssetResponse])
def list_assets(
    type: Optional[str] = None,
    status: Optional[str] = None,
    tag: Optional[str] = None,
    value_contains: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    org: Organization = Depends(verify_api_key)
):
    query = db.query(Asset).filter(Asset.org_id == org.id)

    if type:
        query = query.filter(Asset.type == type)
    if status:
        query = query.filter(Asset.status == status)
    if tag:
        query = query.filter(Asset.tags.contains([tag]))
    if value_contains:
        query = query.filter(Asset.value.contains(value_contains))

    assets = query.offset((page - 1) * page_size).limit(page_size).all()
    return assets


@router.get("/assets/{asset_id}", response_model=AssetResponse)
def get_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    org: Organization = Depends(verify_api_key)
):
    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.org_id == org.id
    ).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.patch("/assets/{asset_id}/stale")
def mark_stale(
    asset_id: str,
    db: Session = Depends(get_db),
    org: Organization = Depends(verify_api_key)
):
    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.org_id == org.id
    ).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    asset.status = AssetStatus.stale
    db.commit()
    return {"message": f"Asset {asset_id} marked as stale"}


@router.get("/assets/{asset_id}/relationships")
def get_relationships(
    asset_id: str,
    db: Session = Depends(get_db),
    org: Organization = Depends(verify_api_key)
):
    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.org_id == org.id
    ).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    related = []
    for r in asset.relationships_from:
        related.append({
            "direction": "outgoing",
            "relationship_type": r.relationship_type,
            "asset": r.to_asset.value
        })
    for r in asset.relationships_to:
        related.append({
            "direction": "incoming",
            "relationship_type": r.relationship_type,
            "asset": r.from_asset.value
        })

    return {"asset": asset.value, "relationships": related}