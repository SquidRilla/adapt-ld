
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
from app.routes import pages, reading, analytics
from app.api import math, attention, auth, reports
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import init_db, seed_data, get_db, User, Question
import random

# Import routers
from app.routes import pages, reading, analytics
from app.api import math, attention, auth, reports, grammar_results

# =========================
# App Initialization
# =========================
app = FastAPI(
    title="ADAPT-LD",
    description="Adaptive Learning & Dyslexia Detection System",
    version="1.0.0"
)

# Initialize DB
async def init_db():
    # Create tables, etc.
    pass

# Seed data
async def seed_data():
    # Add sample questions, users, etc.
    pass

# =========================
# Middleware (CORS)
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# Static Files
# =========================
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# =========================
# Include Routes (Pages)
# =========================
app.include_router(pages.router)
app.include_router(reading.router)
app.include_router(analytics.router)
# =========================
# Include API Routers
# =========================
app.include_router(math.router, prefix="/adapt-ld/math", tags=["Math"])
app.include_router(attention.router, prefix="/adapt-ld/attention", tags=["Attention"])
app.include_router(grammar_results.router, prefix="/adapt-ld/grammar", tags=["Grammar"])
app.include_router(auth.router, prefix="/adapt-ld/auth", tags=["Auth"])
app.include_router(reports.router, prefix="/adapt-ld/reports", tags=["Reports"])

# =========================
# Health Check Route
# =========================
@app.get("/")
async def root():
    return {
        "message": "ADAPT-LD backend is running 🚀"
    }

# =========================
# Optional: Debug Route
# =========================
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "modules": [
            "math",
            "attention",
            "reading",
            "analytics",
            "reports"
        ]
    }



@app.get("/get_question/{test_type}")
async def get_question(test_type: str, db: AsyncSession = Depends(get_db)):
    from sqlalchemy.future import select

    # Get first user
    result = await db.execute(select(User))
    user = result.scalars().first()

    # Get adaptive questions
    result = await db.execute(select(Question).where(
        Question.type == test_type,
        Question.difficulty.between(user.ability_level - 0.2, user.ability_level + 0.2)
    ))
    questions = result.scalars().all()

    if not questions:
        result = await db.execute(select(Question).where(Question.type == test_type))
        questions = result.scalars().all()

    q = random.choice(questions)
    return {"id": q.id, "question": q.question_text}

@app.post("/submit_answer")
async def submit_answer(data: dict, db: AsyncSession = Depends(get_db)):
    from sqlalchemy.future import select

    # Get first user
    result = await db.execute(select(User))
    user = result.scalars().first()

    # Get question
    result = await db.execute(select(Question).where(Question.id == data["question_id"]))
    question = result.scalars().first()

    is_correct = data["answer"] == question.correct_answer

    # Update ability
    if is_correct:
        user.ability_level += 0.1 * (1 - user.ability_level)
    else:
        user.ability_level -= 0.1 * user.ability_level

    db.add(user)
    await db.commit()

    return {"correct": is_correct, "ability": user.ability_level}
