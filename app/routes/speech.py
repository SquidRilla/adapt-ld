
from fastapi import APIRouter, UploadFile, File, Form
from app.services.adapt_speech_service import score_audio
from app.services.adapt_irt_engine import update_theta
from app.services.adapt_ld_classifier import classify_ld
from app.services.adapt_ld_report_generator import generate_adapt_ld_report

router = APIRouter(prefix="/adapt-ld/speech")

@router.post("/score")
async def score_pipeline(
    student_id: str = Form(...),
    theta: float = Form(...),
    expected_text: str = Form(...),
    audio: UploadFile = File(...)
):
    metrics = score_audio(audio, expected_text)
    new_theta = update_theta(theta, metrics["correct"])

    features = {
        "pronunciation_accuracy": metrics["similarity"],
        "reading_wpm": metrics["wpm"],
        "phonological_errors": metrics["phonological_errors"],
        "confidence": metrics["confidence"]
    }

    prediction = classify_ld(features)
    report_file = generate_adapt_ld_report(student_id, metrics, prediction)

    return {
        "theta": new_theta,
        "prediction": prediction,
        "metrics": metrics,
        "report": report_file
    }
