from fastapi import APIRouter
from pydantic import BaseModel
from app.services.attention_service import score_attention

router = APIRouter(prefix="/adapt-ld/attention", tags=["Attention"])

class AttentionSubmission(BaseModel):
    hits: int
    misses: int
    false_alarms: int
    reaction_times: list[float]

@router.post("/score")
def score(data: AttentionSubmission):
    return score_attention(data)