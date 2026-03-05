from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from app.services.numeracy_service import score_numeracy

router = APIRouter(prefix="/adapt-ld/math", tags=["Math"])


class NumeracySubmission(BaseModel):
    answers: List[Optional[float]]
    correct: List[int]
    response_times: List[float]
    total_time: Optional[float] = None
    accuracy: Optional[float] = None


@router.post("/score")
def score_test(data: NumeracySubmission):
    return score_numeracy(data)
