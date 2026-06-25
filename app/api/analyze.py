from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import verify_api_key
from app.langchain_layer.analyzer import (
    natural_language_query,
    risk_scoring,
    enrich_asset,
    generate_report
)
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class QueryRequest(BaseModel):
    question: str

class RiskRequest(BaseModel):
    asset_id: str

class EnrichRequest(BaseModel):
    asset_id: str

class ReportRequest(BaseModel):
    filter_type: Optional[str] = None
    filter_status: Optional[str] = None


@router.post("/analyze/query")
def analyze_query(
    request: QueryRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    return natural_language_query(request.question, db)


@router.post("/analyze/risk")
def analyze_risk(
    request: RiskRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    return risk_scoring(request.asset_id, db)


@router.post("/analyze/enrich")
def analyze_enrich(
    request: EnrichRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    return enrich_asset(request.asset_id, db)


@router.post("/analyze/report")
def analyze_report(
    request: ReportRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    return generate_report(db, request.filter_type, request.filter_status)

from app.cache import llm_cache

@router.get("/cache/stats")
def cache_stats(api_key: str = Depends(verify_api_key)):
    return llm_cache.stats()

@router.delete("/cache/clear")
def cache_clear(api_key: str = Depends(verify_api_key)):
    llm_cache.clear()
    return {"message": "Cache cleared successfully"}