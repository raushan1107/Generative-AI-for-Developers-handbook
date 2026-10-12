"""Drill 01.7: temperature from scratch. Turn scores into probabilities, then sample."""
import math
import random
from collections import Counter

# Scores ("logits") a model might give five candidate words after:
#   "Your exam voucher will arrive ..."
LOGITS = {"soon": 4.0, "tomorrow": 3.2, "today": 2.5, "eventually": 1.0, "never": -1.0}


def softmax(logits, temperature):
    """Divide scores by the temperature, then normalise them into probabilities."""
    scaled = {w: s / temperature for w, s in logits.items()}
    top = max(scaled.values())
    exps = {w: math.exp(s - top) for w, s in scaled.items()}  # subtract the max for numerical safety
    total = sum(exps.values())
    return {w: e / total for w, e in exps.items()}


rng = random.Random(42)
for t in (0.2, 0.7, 1.0, 1.5, 3.0):
    probs = softmax(LOGITS, t)
    picks = Counter(rng.choices(list(probs), weights=list(probs.values()), k=1000))
    print(f"\ntemperature = {t}")
    for word, p in probs.items():
        print(f"  {word:11} {p:6.1%}  {'#' * round(p * 40):40} picked {picks[word]:4} / 1000")
