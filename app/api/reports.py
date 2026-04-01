from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from typing import Dict, Optional
from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.services.adapt_ld_report_generator import generate_adapt_ld_report
from app.services.auth_service import get_current_user_optional
from app.core.database import Test, Response, AttentionResult, Question, get_db

router = APIRouter()

@router.post("/generate")
async def generate_report(data: dict):
    results = data["results"]
    total = len(results)
    correct = sum(1 for r in results if r["correct"])
    total_time = sum(r["rt"] for r in results)

    difficulty_stats = defaultdict(lambda: {"count": 0, "correct": 0, "time": 0})
    for r in results:
        d = difficulty_stats[r["difficulty"]]
        d["count"] += 1
        d["time"] += r["rt"]
        if r["correct"]:
            d["correct"] += 1

    difficulty_report = {
        diff: {
            "accuracy": d["correct"] / d["count"],
            "avg_time": d["time"] / d["count"]
        }
        for diff, d in difficulty_stats.items()
    }

    insights = []
    for diff, d in difficulty_report.items():
        if d["accuracy"] < 0.5:
            insights.append(f"Weakness in {diff}")
        if d["avg_time"] > 5:
            insights.append(f"Slow responses in {diff}")

    return {
        "overall_accuracy": correct / total if total else 0,
        "overall_avg_time": total_time / total if total else 0,
        "difficulty_analysis": difficulty_report,
        "insights": insights
    }

class ReportCreate(BaseModel):
    student_id: str
    images: Optional[Dict[str, str]] = None
    metrics: Optional[Dict[str, float]] = None
    prediction: Optional[str] = None

@router.post("/create")
def create_report(payload: ReportCreate):
    filename = generate_adapt_ld_report(payload.student_id, payload.metrics or {}, payload.prediction or "", images=payload.images)
    return {"filename": filename}

@router.get("/report")
async def report(db: AsyncSession = Depends(get_db)):
    # Query all responses
    responses_result = await db.execute(select(Response))
    responses = responses_result.scalars().all()
    
    if not responses:
        return {
            "overall_accuracy": 0,
            "overall_avg_time": 0,
            "batch_performance": [],
            "difficulty_analysis": {},
            "insights": []
        }
    
    # Calculate overall stats
    total = len(responses)
    correct = sum(1 for r in responses if r.is_correct)
    total_time = sum(r.response_time for r in responses if r.response_time)
    
    # Group by difficulty for analysis
    difficulty_stats = defaultdict(lambda: {"count": 0, "correct": 0, "time": 0})
    for r in responses:
        # Get question to find difficulty
        question_result = await db.execute(select(Question).where(Question.id == r.question_id))
        question = question_result.scalars().first()
        if question:
            d = difficulty_stats[question.difficulty]
            d["count"] += 1
            d["time"] += r.response_time if r.response_time else 0
            if r.is_correct:
                d["correct"] += 1
    
    difficulty_report = {
        str(diff): {
            "accuracy": d["correct"] / d["count"] if d["count"] else 0,
            "avg_time": d["time"] / d["count"] if d["count"] else 0
        }
        for diff, d in difficulty_stats.items()
    }
    
    # Batch performance (group by test, every test)
    tests_result = await db.execute(select(Test))
    tests = tests_result.scalars().all()
    batch_performance = [{"score": t.score / 100.0, "avg_time": 0} for t in tests] if tests else []
    
    insights = []
    for diff, d in difficulty_report.items():
        if d["accuracy"] < 0.5:
            insights.append(f"Weakness in difficulty {diff}")
        if d["avg_time"] > 5:
            insights.append(f"Slow responses in difficulty {diff}")
    
    return {
        "overall_accuracy": correct / total if total else 0,
        "overall_avg_time": total_time / total if total else 0,
        "batch_performance": batch_performance,
        "difficulty_analysis": difficulty_report,
        "insights": insights
    }

@router.get("/test-scores")
async def get_test_scores(request: Request, db: AsyncSession = Depends(get_db)):
    """Fetch test scores grouped by type for current user (if authenticated)."""
    user = await get_current_user_optional(request, db)
    
    if not user:
        # Return empty if not logged in
        return {}
    
    # Query all tests for this user
    tests_result = await db.execute(
        select(Test)
        .where(Test.user_id == user.id)
        .order_by(Test.created_at.desc())
    )
    tests = tests_result.scalars().all()
    
    # Group by test_type and get the latest score for each
    test_scores = {}
    for test in tests:
        if test.test_type not in test_scores:
            test_scores[test.test_type] = {
                "score": float(test.score),
                "date": test.created_at.isoformat() if test.created_at else None,
                "test_id": test.id
            }
    
    return test_scores
