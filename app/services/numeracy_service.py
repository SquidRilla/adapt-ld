from typing import Dict, List


def score_numeracy(data) -> Dict:
    """Compute numeracy metrics from submitted data.

    Expected `data` fields:
      - answers: list of submitted numeric answers (floats/ints)
      - correct: list of expected numeric answers (floats/ints) OR correctness flags (1/0)
      - response_times: list of floats (seconds)

    Returns a dictionary with accuracy, average response time, total, correct_count,
    and a normalized `number_sense_score` (0-100).
    """
    # Normalize inputs if dict-like
    if isinstance(data, dict):
        answers = data.get('answers', [])
        correct = data.get('correct', [])
        rts = data.get('response_times', [])
    else:
        # pydantic model with attributes
        answers = list(getattr(data, 'answers', []))
        correct = list(getattr(data, 'correct', []))
        rts = list(getattr(data, 'response_times', []))

    total = max(len(answers), len(correct))
    # If `correct` contains expected answers (not flags), derive correctness
    correctness_flags: List[int] = []
    if all(isinstance(x, (int, float)) for x in correct) and len(correct) > 0:
        for a, c in zip(answers, correct):
            try:
                correctness_flags.append(1 if float(a) == float(c) else 0)
            except Exception:
                correctness_flags.append(0)
    else:
        # assume correct already contains flags
        correctness_flags = [1 if int(x) else 0 for x in correct[:len(answers)]]

    correct_count = sum(correctness_flags) if correctness_flags else 0
    accuracy = (correct_count / total) if total > 0 else 0.0

    avg_rt = (sum(rts) / len(rts)) if rts else 0.0

    # number_sense_score combines accuracy and speed (lower RT is better)
    # base score 0..1
    base = 0.7 * accuracy + 0.3 * (1 / (1 + avg_rt)) if total > 0 else 0.0
    number_sense_score = round(base * 100, 1)

    return {
        'total': total,
        'correct': correct_count,
        'accuracy': round(accuracy, 3),
        'avg_response_time': round(avg_rt, 3),
        'number_sense_score': number_sense_score,
    }
