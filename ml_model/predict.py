"""
ADAPT-LD — Inference Module
============================
Load trained model and predict risk level for new student assessments.

Usage:
    python predict.py                    # runs built-in demo
    from predict import predict_student  # import in your app
"""

import json
import numpy as np
import pandas as pd
import joblib
from pathlib import Path

BASE   = Path(__file__).parent
MODELS = BASE / "models"


def load_model():
    """Load trained model, scaler, and metadata."""
    model  = joblib.load(MODELS / "adapt_ld_rf_model.pkl")
    scaler = joblib.load(MODELS / "adapt_ld_scaler.pkl")
    with open(MODELS / "adapt_ld_metadata.json") as f:
        meta = json.load(f)
    return model, scaler, meta


def predict_student(
    reading_accuracy: float,
    writing_coherence: float,
    math_accuracy: float,
    speech_fluency: float,
    attention_response_ms: float,
    age: float,
    repeated_errors: int,
    assessment_duration_s: float,
) -> dict:
    """
    Predict the LD risk level for a single student.

    Parameters
    ----------
    reading_accuracy      : 0–100  (% correct)
    writing_coherence     : 0–100  (% score)
    math_accuracy         : 0–100  (% correct)
    speech_fluency        : 0–100  (% score)
    attention_response_ms : reaction time in milliseconds (200–2000)
    age                   : student age in years (6–18)
    repeated_errors       : count of repeated errors (0–20)
    assessment_duration_s : total assessment time in seconds

    Returns
    -------
    dict with keys:
        risk_level  : int (0–3)
        risk_label  : str ("No Risk" / "Mild Risk" / …)
        confidence  : float (0–1)
        probabilities: dict {label: probability}
        interpretation: str  clinical note
    """
    model, scaler, meta = load_model()
    features = meta["features"]
    label_map = {int(k): v for k, v in meta["label_map"].items()}

    # Derived features (must match training)
    academic_composite = (reading_accuracy + writing_coherence + math_accuracy) / 3
    processing_speed   = 1 / (attention_response_ms / 1000 + 1e-6)
    error_rate_norm    = repeated_errors / (assessment_duration_s / 60 + 1e-6)

    raw = {
        "reading_accuracy":      reading_accuracy,
        "writing_coherence":     writing_coherence,
        "math_accuracy":         math_accuracy,
        "speech_fluency":        speech_fluency,
        "attention_response_ms": attention_response_ms,
        "age":                   age,
        "repeated_errors":       repeated_errors,
        "assessment_duration_s": assessment_duration_s,
        "academic_composite":    academic_composite,
        "processing_speed":      processing_speed,
        "error_rate_norm":       error_rate_norm,
    }

    X = pd.DataFrame([raw])[features]
    X_sc = scaler.transform(X)

    risk_int   = int(model.predict(X_sc)[0])
    proba      = model.predict_proba(X_sc)[0]
    confidence = float(proba[risk_int])

    prob_dict = {label_map[i]: round(float(p), 4) for i, p in enumerate(proba)}

    interpretations = {
        0: "No significant LD indicators detected. Continue regular monitoring.",
        1: "Mild patterns observed. Consider closer monitoring and differentiated instruction.",
        2: "Moderate indicators present. Recommend targeted intervention and specialist review.",
        3: "Strong LD indicators detected. Urgent referral for comprehensive professional evaluation recommended.",
    }

    return {
        "risk_level":      risk_int,
        "risk_label":      label_map[risk_int],
        "confidence":      round(confidence, 4),
        "probabilities":   prob_dict,
        "interpretation":  interpretations[risk_int],
    }


# ── Demo ─────────────────────────────────────────────
if __name__ == "__main__":
    demo_students = [
        {
            "name": "Student A — Typical Learner",
            "data": dict(reading_accuracy=88, writing_coherence=85, math_accuracy=82,
                         speech_fluency=87, attention_response_ms=380, age=10,
                         repeated_errors=1, assessment_duration_s=210),
        },
        {
            "name": "Student B — Mild Difficulties",
            "data": dict(reading_accuracy=68, writing_coherence=65, math_accuracy=70,
                         speech_fluency=72, attention_response_ms=620, age=9,
                         repeated_errors=5, assessment_duration_s=280),
        },
        {
            "name": "Student C — Moderate Risk (Dyslexia-like)",
            "data": dict(reading_accuracy=48, writing_coherence=45, math_accuracy=72,
                         speech_fluency=60, attention_response_ms=850, age=11,
                         repeated_errors=9, assessment_duration_s=350),
        },
        {
            "name": "Student D — High Risk",
            "data": dict(reading_accuracy=28, writing_coherence=30, math_accuracy=35,
                         speech_fluency=38, attention_response_ms=1400, age=8,
                         repeated_errors=16, assessment_duration_s=500),
        },
    ]

    RISK_COLORS = {
        "No Risk":        "\033[92m",   # green
        "Mild Risk":      "\033[93m",   # yellow
        "Moderate Risk":  "\033[33m",   # orange-ish
        "High Risk":      "\033[91m",   # red
    }
    RESET = "\033[0m"

    print("\n" + "="*65)
    print("  ADAPT-LD  |  Student Risk Prediction Demo")
    print("="*65)

    for s in demo_students:
        result = predict_student(**s["data"])
        color  = RISK_COLORS.get(result["risk_label"], "")
        print(f"\n  {s['name']}")
        print(f"  {'─'*55}")
        print(f"  Risk Level   : {color}{result['risk_label']}{RESET}  (confidence {result['confidence']*100:.1f}%)")
        print(f"  Probabilities:")
        for lbl, p in result["probabilities"].items():
            bar = "█" * int(p * 30)
            print(f"    {lbl:15s}  {bar:<30s}  {p*100:5.1f}%")
        print(f"  Interpretation: {result['interpretation']}")

    print("\n" + "="*65 + "\n")
