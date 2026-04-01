from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.services.auth_service import get_current_user
from app.core.database import Test, Response, AttentionResult, get_db
import sys
from pathlib import Path

# Add ml_model to path
ML_MODEL_PATH = Path(__file__).parent.parent.parent / "ml_model"
sys.path.insert(0, str(ML_MODEL_PATH))

try:
    from predict import predict_student
except ImportError as e:
    print(f"Warning: Could not import ML model: {e}")
    predict_student = None

router = APIRouter(tags=["ML Prediction"])

class PredictionRequest(BaseModel):
    """Request payload for LD risk prediction"""
    reading_accuracy: float = 0.5
    writing_coherence: float = 0.5
    math_accuracy: float = 0.5
    speech_fluency: float = 0.5
    attention_response_ms: float = 500
    age: float = 10
    repeated_errors: int = 0
    assessment_duration_s: float = 300

@router.post("/predict")
async def predict_ld_risk(
    request: PredictionRequest,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Predict LD risk level for current user based on assessment scores.
    
    Uses user's latest test scores if they exist, otherwise uses provided values.
    """
    if not predict_student:
        raise HTTPException(status_code=500, detail="ML model not available")
    
    # Optionally fetch user's latest scores from database
    test_result = await db.execute(
        select(Test).where(Test.user_id == user.id).order_by(Test.created_at.desc())
    )
    latest_tests = test_result.scalars().all()
    
    # Build score dict from latest tests
    scores = {
        "reading_accuracy": request.reading_accuracy,
        "writing_coherence": request.writing_coherence,
        "math_accuracy": request.math_accuracy,
        "speech_fluency": request.speech_fluency,
    }
    
    # Override with database values if available
    for test in latest_tests:
        if test.test_type == "reading":
            scores["reading_accuracy"] = test.score
        elif test.test_type == "grammar":
            scores["writing_coherence"] = test.score
        elif test.test_type == "numeracy":
            scores["math_accuracy"] = test.score
        elif test.test_type == "speech":
            scores["speech_fluency"] = test.score
    
    # Fetch attention data
    attention_result = await db.execute(
        select(AttentionResult)
        .where(AttentionResult.user_id == user.id)
        .order_by(AttentionResult.created_at.desc())
        .limit(1)
    )
    latest_attention = attention_result.scalars().first()
    
    # Calculate attention response time
    attention_response_ms = request.attention_response_ms
    if latest_attention and latest_attention.avg_reaction_time:
        attention_response_ms = latest_attention.avg_reaction_time * 1000
    
    # Call ML model
    try:
        result = predict_student(
            reading_accuracy=scores["reading_accuracy"],
            writing_coherence=scores["writing_coherence"],
            math_accuracy=scores["math_accuracy"],
            speech_fluency=scores["speech_fluency"],
            attention_response_ms=attention_response_ms,
            age=request.age,
            repeated_errors=request.repeated_errors,
            assessment_duration_s=request.assessment_duration_s,
        )
        return {
            "user_id": user.id,
            "prediction": result,
            "scores_used": scores,
            "attention_response_ms": attention_response_ms,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@router.get("/predict-summary")
async def get_prediction_summary(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get latest LD risk prediction without requiring a new assessment.
    Uses existing stored scores.
    """
    if not predict_student:
        raise HTTPException(status_code=500, detail="ML model not available")
    
    # Fetch all test scores
    test_result = await db.execute(
        select(Test).where(Test.user_id == user.id).order_by(Test.created_at.desc())
    )
    tests = test_result.scalars().all()
    
    # Extract latest score for each type
    scores = {
        "reading_accuracy": 50,
        "writing_coherence": 50,
        "math_accuracy": 50,
        "speech_fluency": 50,
    }
    
    for test in tests:
        if test.test_type == "reading" and "reading_accuracy" in scores:
            scores["reading_accuracy"] = test.score
        elif test.test_type == "grammar" and "writing_coherence" in scores:
            scores["writing_coherence"] = test.score
        elif test.test_type == "numeracy" and "math_accuracy" in scores:
            scores["math_accuracy"] = test.score
        elif test.test_type == "speech" and "speech_fluency" in scores:
            scores["speech_fluency"] = test.score
    
    # Fetch latest attention data
    attention_result = await db.execute(
        select(AttentionResult)
        .where(AttentionResult.user_id == user.id)
        .order_by(AttentionResult.created_at.desc())
        .limit(1)
    )
    latest_attention = attention_result.scalars().first()
    attention_response_ms = latest_attention.avg_reaction_time * 1000 if latest_attention else 500
    
    try:
        result = predict_student(
            reading_accuracy=scores["reading_accuracy"],
            writing_coherence=scores["writing_coherence"],
            math_accuracy=scores["math_accuracy"],
            speech_fluency=scores["speech_fluency"],
            attention_response_ms=attention_response_ms,
            age=10,  # Default age, could be stored in User model
            repeated_errors=0,
            assessment_duration_s=300,
        )
        return {
            "user_id": user.id,
            "prediction": result,
            "scores": scores,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")
