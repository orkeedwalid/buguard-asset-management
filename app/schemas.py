from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class AssetCreate(BaseModel):
    id: Optional[str] = None
    type: str
    value: str
    status: Optional[str] = "active"
    source: Optional[str] = "import"
    tags: Optional[List[str]] = []
    metadata: Optional[Dict[str, Any]] = {}

class AssetResponse(BaseModel):
    id: str
    type: str
    value: str
    status: str
    first_seen: datetime
    last_seen: datetime
    source: str
    tags: Optional[List[str]] = []
    metadata_: Optional[Dict[str, Any]] = {}

    class Config:
        from_attributes = True

class BulkImportRequest(BaseModel):
    assets: List[AssetCreate]