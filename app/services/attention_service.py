def score_attention(data):
    total_targets = data.hits + data.misses

    hit_rate = data.hits / total_targets if total_targets else 0
    impulsivity = data.false_alarms / (data.false_alarms + data.hits + 1)

    avg_rt = sum(data.reaction_times)/len(data.reaction_times) if data.reaction_times else 0

    attention_score = round(hit_rate * 0.5 + (1-impulsivity)*0.3 + (1/(1+avg_rt))*0.2, 3)

    return {
        "hit_rate": round(hit_rate, 3),
        "impulsivity_index": round(impulsivity, 3),
        "attention_score": attention_score
    }
