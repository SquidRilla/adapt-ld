

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

# Install the requests package by executing the command "pip install requests"

import requests
import time

base_url = "https://api.assemblyai.com"

headers = {
    "authorization": "d24307dd6d294687b659d5a13880601c"
}
# You can upload a local file using the following code
# with open("./my-audio.mp3", "rb") as f:
#   response = requests.post(base_url + "/v2/upload",
#                           headers=headers,
#                           data=f)
# 
# audio_url = response.json()["upload_url"]

audio_url = "https://assembly.ai/wildfires.mp3"


data = {
    "audio_url": audio_url,
    "language_detection": True,
    # Uses universal-3-pro for en, es, de, fr, it, pt. Else uses universal-2 for support across all other languages
    "speech_models": ["universal-3-pro", "universal-2"]
}

url = base_url + "/v2/transcript"
response = requests.post(url, json=data, headers=headers)

transcript_id = response.json()['id']
polling_endpoint = base_url + "/v2/transcript/" + transcript_id

while True:
  transcription_result = requests.get(polling_endpoint, headers=headers).json()
  transcript_text = transcription_result['text']

  if transcription_result['status'] == 'completed':
    print(f"Transcript Text:", transcript_text)
    break

  elif transcription_result['status'] == 'error':
    raise RuntimeError(f"Transcription failed: {transcription_result['error']}")

  else:
    time.sleep(3)