from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.attention_service import score_attention
from app.services.auth_service import get_current_user
from app.core.database import AttentionResult, get_db

router = APIRouter(prefix="/adapt-ld/attention", tags=["Attention"])

class AttentionSubmission(BaseModel):
    hits: int
    misses: int
    false_alarms: int
    reaction_times: list[float]

@router.post("/score")
async def score(data: AttentionSubmission, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = score_attention(data)
    
    # Save attention result
    attention_result = AttentionResult(
        user_id=user.id,
        hits=data.hits,
        misses=data.misses,
        false_alarms=data.false_alarms,
        avg_reaction_time=sum(data.reaction_times) / len(data.reaction_times) if data.reaction_times else 0
    )
    db.add(attention_result)
    await db.commit()
    
    return result