
from fastapi import APIRouter

router = APIRouter(prefix="/adapt-ld/admin/analytics")

@router.get("/overview")
def overview():
    return {
        "total_students": 10,
        "flagged_rate": 0.3,
        "average_fluency": 105.4
    }

