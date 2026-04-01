from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class GrammarResult(BaseModel):
    score:int
    questions:int

@router.post("/api/grammar_results")
def save_results(data:GrammarResult):

    print(data)

    return {"status":"saved"}