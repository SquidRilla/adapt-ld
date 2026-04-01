from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.services.numeracy_service import score_numeracy
from app.services.auth_service import get_current_user
from app.core.database import Test, Response, get_db

router = APIRouter(prefix="/adapt-ld/math", tags=["Math"])

class NumeracySubmission(BaseModel):
    answers: List[Optional[float]]
    correct: List[int]
    response_times: List[float]
    total_time: Optional[float] = None
    accuracy: Optional[float] = None

@router.post("/score")
async def score_test(data: NumeracySubmission, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Score the test
    result = score_numeracy(data)
    
    # Save test result
    test = Test(user_id=user.id, test_type="numeracy", score=result.get("number_sense_score", 0))
    db.add(test)
    await db.commit()
    await db.refresh(test)
    
    # Save individual responses
    for i, (ans, corr, rt) in enumerate(zip(data.answers, data.correct, data.response_times)):
        response = Response(
            user_id=user.id,
            question_id=i,  # dummy, since no question table
            is_correct=bool(corr),
            response_time=rt
        )
        db.add(response)
    await db.commit()
    
    return result
