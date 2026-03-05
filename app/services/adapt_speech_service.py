
"""
Speech scoring service.

This attempts to use OpenAI Whisper (openai-whisper) to transcribe uploaded audio
and compute simple metrics (similarity, wpm, phonological error estimate).

If Whisper is not installed, it falls back to the original demo randomized scorer
so the app remains functional.

Notes for production:
- Install `openai-whisper` and its dependencies (torch, ffmpeg available on PATH).
- Consider using a smaller model for faster local scoring (`small`, `base`) or run
  ASR as a separate service if resources are constrained.
"""
import os
import tempfile
import difflib
import random
from typing import Dict

try:
    import whisper
    _HAS_WHISPER = True
except Exception:
    _HAS_WHISPER = False


def _demo_score(expected_text: str) -> Dict:
    # lightweight fallback used when Whisper isn't available
    similarity = random.uniform(0.7, 0.95)
    errors = int((1 - similarity) * 5)
    wpm = random.uniform(70, 140)
    confidence = 0.7 * similarity + 0.3 * min(wpm / 120, 1)
    return {
        "spoken_text": expected_text,
        "similarity": similarity,
        "phonological_errors": errors,
        "wpm": wpm,
        "confidence": confidence,
        "correct": similarity > 0.75,
    }


def score_audio(upload_file, expected_text: str) -> Dict:
    """Score an uploaded audio `UploadFile` against `expected_text`.

    Returns a dict with keys: spoken_text, similarity, phonological_errors, wpm,
    confidence, correct
    """
    # If Whisper not available, return demo result
    if not _HAS_WHISPER:
        return _demo_score(expected_text)

    # Save upload to a temporary file
    suffix = os.path.splitext(getattr(upload_file, "filename", "audio"))[1] or ".webm"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        # write bytes to temp file
        content = upload_file.file.read()
        tmp.write(content)
        tmp.flush()
        tmp.close()

        # load whisper model (use small for reasonable speed)
        model = whisper.load_model("small")
        # transcribe
        result = model.transcribe(tmp.name)
        transcript = (result.get("text") or "").strip()

        # estimate duration from segments if available
        segments = result.get("segments") or []
        duration = 0.0
        if segments:
            duration = segments[-1].get("end", 0.0)
        else:
            # fallback: use audio length via whisper's audio loader if possible
            try:
                audio = whisper.load_audio(tmp.name)
                duration = len(audio) / whisper.audio.SAMPLE_RATE
            except Exception:
                duration = 0.0

        words = transcript.split()
        wpm = (len(words) / duration * 60.0) if duration > 0 else 0.0

        # similarity using SequenceMatcher
        similarity = difflib.SequenceMatcher(None, expected_text.lower(), transcript.lower()).ratio()

        # phonological errors: rough heuristic from similarity
        phonological_errors = max(0, int(round((1 - similarity) * max(1, len(expected_text.split())))))

        # confidence: proxy combining similarity and speaking rate
        confidence = 0.8 * similarity + 0.2 * min(wpm / 140.0, 1.0)

        return {
            "spoken_text": transcript,
            "similarity": float(similarity),
            "phonological_errors": int(phonological_errors),
            "wpm": float(wpm),
            "confidence": float(confidence),
            "correct": similarity > 0.75,
        }
    finally:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass
