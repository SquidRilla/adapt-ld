
from fastapi import APIRouter

router = APIRouter(prefix="/adapt-ld/assessment")

ITEMS = [
    {"text": "cat", "difficulty": -2},
    {"text": "bread", "difficulty": -1},
    {"text": "school", "difficulty": 0},
    {"text": "knife", "difficulty": 1.5},
]

@router.post("/start")
def start():
    return {"theta": 0.0}

@router.post("/next-item")
def next_item(payload: dict):
    theta = payload.get("theta", 0)
    used_items = payload.get("used_items", [])
    
    # Filter out already used items
    available_items = [item for item in ITEMS if item["text"] not in used_items]
    
    if not available_items:
        # If all items used, reset and pick any
        available_items = ITEMS
    
    # Select item closest to current theta (adaptive difficulty)
    item = min(available_items, key=lambda i: abs(i["difficulty"] - theta))
    return item

@router.post("/submit-response")
def submit_response(payload: dict):
    """Update theta based on whether answer was correct"""
    theta = payload.get("theta", 0)
    is_correct = payload.get("is_correct", False)
    
    # Simple IRT-like update: increase theta if correct, decrease if incorrect
    theta_delta = 0.3 if is_correct else -0.3
    new_theta = theta + theta_delta
    
    return {"theta": new_theta}
