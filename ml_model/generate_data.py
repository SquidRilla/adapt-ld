"""
ADAPT-LD — Synthetic Dataset Generator
======================================
Generates a realistic student assessment dataset for training and evaluation.

Features:
  - reading_accuracy      (0–100)
  - writing_coherence     (0–100)
  - math_accuracy         (0–100)
  - speech_fluency        (0–100)
  - attention_response_ms (200–2000 ms, lower = better)
  - age                   (6–18)
  - repeated_errors       (0–20)
  - assessment_duration_s (60–600 s)

Target (risk_level):
  0 = No Risk
  1 = Mild Risk
  2 = Moderate Risk
  3 = High Risk
"""

import numpy as np
import pandas as pd
from pathlib import Path

np.random.seed(42)

N = 2000
OUTPUT = Path(__file__).parent / "data" / "student_assessments.csv"
OUTPUT.parent.mkdir(exist_ok=True)


def generate_profile(risk: int, n: int) -> pd.DataFrame:
    """Generate n samples for a given risk class."""
    # Base distributions shift by risk level
    r = risk  # 0,1,2,3

    reading   = np.clip(np.random.normal(85 - r*18, 10, n), 0, 100)
    writing   = np.clip(np.random.normal(82 - r*17, 11, n), 0, 100)
    math      = np.clip(np.random.normal(80 - r*16, 12, n), 0, 100)
    speech    = np.clip(np.random.normal(83 - r*15, 10, n), 0, 100)
    attn_ms   = np.clip(np.random.normal(350 + r*320, 100, n), 200, 2000)
    age       = np.random.randint(6, 19, n).astype(float)
    errors    = np.clip(np.random.poisson(r * 3.5 + 0.5, n), 0, 20).astype(float)
    duration  = np.clip(np.random.normal(180 + r*60, 60, n), 60, 600)

    df = pd.DataFrame({
        "reading_accuracy":      np.round(reading, 1),
        "writing_coherence":     np.round(writing, 1),
        "math_accuracy":         np.round(math, 1),
        "speech_fluency":        np.round(speech, 1),
        "attention_response_ms": np.round(attn_ms, 0),
        "age":                   age,
        "repeated_errors":       errors,
        "assessment_duration_s": np.round(duration, 0),
        "risk_level":            r,
    })
    return df


# Class sizes: slightly imbalanced (realistic)
sizes = [600, 500, 500, 400]
parts = [generate_profile(r, n) for r, n in enumerate(sizes)]
df = pd.concat(parts, ignore_index=True).sample(frac=1, random_state=42).reset_index(drop=True)

df.to_csv(OUTPUT, index=False)
print(f"Dataset saved → {OUTPUT}")
print(df["risk_level"].value_counts().sort_index().rename({0:"No Risk",1:"Mild",2:"Moderate",3:"High"}))
print(f"\nShape: {df.shape}")
print(df.describe().round(2).to_string())
