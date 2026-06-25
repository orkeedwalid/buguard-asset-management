from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Asset, AssetRelationship, AssetStatus
from app.schemas import AssetCreate, AssetResponse, BulkImportRequest
from app.auth import verify_api_key
from datetime import datetime, timezone
from typing import List, Optional

def utcnow():
    return datetime.now(timezone.utc)

router = APIRouter()

@router.post("/import")
def bulk_import(
    request: BulkImportRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)):
    imported = 0
    updated = 0
    failed = 0
    errors = []

    for item in request.assets:
        try:
            # Check required fields
            if not item.value or not item.type:
                failed += 1
                errors.append(f"Missing required fields for asset: {item}")
                continue

            # Deduplication — check if asset already exists by value and type
            existing = db.query(Asset).filter(
                Asset.value == item.value,
                Asset.type == item.type
            ).first()

            if existing:
                # Update last_seen and merge tags and metadata
                existing.last_seen = utcnow()
                existing.tags = list(set((existing.tags or []) + (item.tags or [])))
                existing.metadata_ = {**(existing.metadata_ or {}), **(item.metadata or {})}
                # If asset was stale, mark it active again
                if existing.status == AssetStatus.stale:
                    existing.status = AssetStatus.active
                updated += 1
            else:
                # Create new asset
                asset = Asset(
                    id=item.id or None,
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
    db: Session = Depends(get_db)
):
    query = db.query(Asset)

    if type:
        query = query.filter(Asset.type == type)
    if status:
        query = query.filter(Asset.status == status)
    if tag:
        query = query.filter(Asset.tags.contains([tag]))
    if value_contains:
        query = query.filter(Asset.value.contains(value_contains))

    total = query.count()
    assets = query.offset((page - 1) * page_size).limit(page_size).all()

    return assets


@router.get("/assets/{asset_id}", response_model=AssetResponse)
def get_asset(asset_id: str, db: Session = Depends(get_db)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.patch("/assets/{asset_id}/stale")
def mark_stale(asset_id: str, db: Session = Depends(get_db)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    asset.status = AssetStatus.stale
    db.commit()
    return {"message": f"Asset {asset_id} marked as stale"}


@router.get("/assets/{asset_id}/relationships")
def get_relationships(asset_id: str, db: Session = Depends(get_db)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
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