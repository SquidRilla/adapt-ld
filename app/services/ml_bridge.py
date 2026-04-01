"""
Bridge module to integrate ML model predictions into the app.
"""

import sys
from pathlib import Path

# Add ml_model to path
ML_MODEL_PATH = Path(__file__).parent.parent.parent / "ml_model"
sys.path.insert(0, str(ML_MODEL_PATH))

from predict import predict_student


async def get_student_ld_prediction(
    reading_accuracy: float = 0,
    writing_coherence: float = 0,
    math_accuracy: float = 0,
    speech_fluency: float = 0,
    attention_response_ms: float = 600,
    age: float = 12,
    repeated_errors: int = 0,
    assessment_duration_s: float = 300,
) -> dict:
    """
    Predict LD risk for a student using the trained ML model.
    
    Returns:
        {
            'risk_level': 0-3,
            'risk_label': str,
            'confidence': float 0-1,
            'probabilities': dict,
            'interpretation': str
        }
    """
    try:
        prediction = predict_student(
            reading_accuracy=reading_accuracy,
            writing_coherence=writing_coherence,
            math_accuracy=math_accuracy,
            speech_fluency=speech_fluency,
            attention_response_ms=attention_response_ms,
            age=age,
            repeated_errors=repeated_errors,
            assessment_duration_s=assessment_duration_s,
        )
        return prediction
    except Exception as e:
        print(f"Error during ML prediction: {e}")
        return {
            "risk_level": 0,
            "risk_label": "Unknown",
            "confidence": 0.0,
            "probabilities": {},
            "interpretation": f"Error: {str(e)}",
        }
