
def classify_ld(features: dict):
    # Speech-based checks (primary)
    speech_risk = 0
    if features.get("pronunciation_accuracy", 1) < 0.78:
        speech_risk += 1
    if features.get("reading_wpm", 200) < 85:
        speech_risk += 1
    if features.get("phonological_errors", 0) > 2:
        speech_risk += 1
    if features.get("confidence", 1) < 0.65:
        speech_risk += 1

    # Auxiliary checks (supporting evidence)
    aux_risk = 0
    if "attention_score" in features and features.get("attention_score") is not None:
        if features.get("attention_score") < 0.6:
            aux_risk += 1
    if "numeracy_score" in features and features.get("numeracy_score") is not None:
        # numeracy_score expected 0-100
        if features.get("numeracy_score") < 65:
            aux_risk += 1

    # Combine with weighting: speech carries primary weight, aux provides supporting evidence
    final_score = float(speech_risk) + 0.75 * float(aux_risk)

    # Decision threshold (tunable)
    if final_score >= 2.5:
        return "Likely Dyslexia"
    return "No LD Detected"
