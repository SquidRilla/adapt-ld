from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.auth_service import get_current_user
from app.core.database import Test, Response, get_db

router = APIRouter(tags=["Grammar"])

class GrammarResult(BaseModel):
    score: int
    total_questions: int
    correct_answers: int
    response_time: float = 0

@router.post("/score")
async def save_grammar_test(data: GrammarResult, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Save grammar test score to database."""
    
    # Convert score to percentage (0-100)
    score_percentage = (data.correct_answers / data.total_questions * 100) if data.total_questions > 0 else 0
    
    # Save test result
    test = Test(
        user_id=user.id,
        test_type="grammar",
        score=score_percentage
    )
    db.add(test)
    await db.commit()
    await db.refresh(test)
    
    return {
        "status": "saved",
        "test_id": test.id,
        "score": score_percentage,
        "message": f"Grammar test saved: {data.correct_answers}/{data.total_questions} correct"
    }