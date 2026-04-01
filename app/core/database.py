import psycopg2
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from datetime import datetime

def get_db_connection():
    return psycopg2.connect(
        dbname="adapt_ld",
        user="postgres",
        password="9090",
        host="localhost",
        port="5432"
    )

DATABASE_URL = "postgresql+asyncpg://postgres:9090@localhost:5432/adapt_ld"

# Async Engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Async Session
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

# ----------------------
# MODELS
# ----------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    email = Column(String(120), unique=True)
    password_hash = Column(String(200))
    ability_level = Column(Float, default=0.5)
    created_at = Column(DateTime, default=datetime.utcnow)

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50))
    topic = Column(String(50))
    question_text = Column(Text)
    correct_answer = Column(String(200))
    difficulty = Column(Float)

class Response(Base):
    __tablename__ = "responses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    question_id = Column(Integer)
    is_correct = Column(Boolean)
    response_time = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class Test(Base):
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    test_type = Column(String(50))
    score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class AttentionResult(Base):
    __tablename__ = "attention_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    hits = Column(Integer)
    misses = Column(Integer)
    false_alarms = Column(Integer)
    avg_reaction_time = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

# ----------------------
# DEPENDENCY
# ----------------------
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# ----------------------
# INIT & SEED
# ----------------------
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def seed_data():
    from sqlalchemy.future import select
    async with AsyncSessionLocal() as db:
        # Check if data exists
        result = await db.execute(select(User))
        user_exists = result.scalars().first()
        if user_exists:
            return

        # Add default user
        from app.services.auth_service import pwd_context
        hashed_password = pwd_context.hash("password")
        user = User(name="Student", email="student@test.com", password_hash=hashed_password, ability_level=0.5)
        db.add(user)

        # Add questions
        questions = [
            Question(type="grammar", topic="verb", question_text="She ___ to school.", correct_answer="goes", difficulty=0.3),
            Question(type="grammar", topic="tense", question_text="I ___ eating now.", correct_answer="am", difficulty=0.3),
            Question(type="grammar", topic="tense", question_text="They ___ playing football.", correct_answer="are", difficulty=0.6),
            Question(type="grammar", topic="agreement", question_text="Neither of them ___ ready.", correct_answer="is", difficulty=0.6),
            Question(type="grammar", topic="conditional", question_text="Had I known, I ___ acted.", correct_answer="would have", difficulty=0.9),
            Question(type="grammar", topic="modal", question_text="You ___ have told me earlier.", correct_answer="should", difficulty=0.8),
            Question(type="reading", topic="comprehension", question_text="What is the main idea?", correct_answer="central idea", difficulty=0.5),
            Question(type="math", topic="arithmetic", question_text="5 + 7 = ?", correct_answer="12", difficulty=0.2),
        ]
        db.add_all(questions)
        await db.commit()
        print("✅ Async DB seeded!")