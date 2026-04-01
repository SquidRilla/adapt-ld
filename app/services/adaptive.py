import random
from fastapi import Depends, FastAPI, FastAPI
from sqlalchemy.orm import Session
from app.core.database import get_db, Question, User

app= FastAPI()

def update_ability(user, is_correct, response_time):

    if is_correct:
        boost = 0.15 if response_time < 2 else 0.08
        user.ability += boost * (1 - user.ability)
    else:
        user.ability -= 0.1 * user.ability

    user.ability = max(0, min(1, user.ability))


def pick_question(questions, ability):

    filtered = [
        q for q in questions
        if abs(q.difficulty - ability) <= 0.2
    ]

    if not filtered:
        filtered = questions

    return random.choice(filtered)



@app.get("/get_question/{test_type}")
def get_question(test_type: str, db: Session = Depends(get_db)):
    user = db.query(User).first()

    questions = db.query(Question).filter(
        Question.type == test_type,
        Question.difficulty.between(user.ability_level - 0.2, user.ability_level + 0.2)
    ).all()

    if not questions:
        questions = db.query(Question).filter_by(type=test_type).all()

    q = random.choice(questions)

    return {"id": q.id, "question": q.question_text}

@app.post("/submit_answer")
def submit_answer(data: dict, db: Session = Depends(get_db)):
    user = db.query(User).first()
    question = db.query(Question).get(data["question_id"])

    is_correct = data["answer"] == question.correct_answer

    # update ability
    if is_correct:
        user.ability_level += 0.1 * (1 - user.ability_level)
    else:
        user.ability_level -= 0.1 * user.ability_level

    db.commit()

    return {
        "correct": is_correct,
        "ability": user.ability_level
    }