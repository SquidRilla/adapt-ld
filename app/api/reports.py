from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Optional
from app.services.adapt_ld_report_generator import generate_adapt_ld_report

router = APIRouter(prefix="/adapt-ld/report", tags=["Reports"])


class ReportCreate(BaseModel):
    student_id: str
    images: Optional[Dict[str, str]] = None
    metrics: Optional[Dict[str, float]] = None
    prediction: Optional[str] = None


@router.post("/create")
def create_report(payload: ReportCreate):
    filename = generate_adapt_ld_report(payload.student_id, payload.metrics or {}, payload.prediction or "", images=payload.images)
    return {"filename": filename}
