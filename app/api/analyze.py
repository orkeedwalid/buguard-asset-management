from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
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
def analyze_query(request: QueryRequest, db: Session = Depends(get_db)):
    return natural_language_query(request.question, db)


@router.post("/analyze/risk")
def analyze_risk(request: RiskRequest, db: Session = Depends(get_db)):
    return risk_scoring(request.asset_id, db)


@router.post("/analyze/enrich")
def analyze_enrich(request: EnrichRequest, db: Session = Depends(get_db)):
    return enrich_asset(request.asset_id, db)


@router.post("/analyze/report")
def analyze_report(request: ReportRequest, db: Session = Depends(get_db)):
    return generate_report(db, request.filter_type, request.filter_status)