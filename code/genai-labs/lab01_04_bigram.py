"""Drill 01.4: a toy next-word predictor. The great-great-grandparent of an LLM."""
import random
from collections import Counter, defaultdict

CORPUS = """
the course starts on monday . the course includes hands-on labs .
the labs run on azure . the exam voucher arrives after the course .
the voucher is valid for twelve months . the labs are available for thirty days .
the course is online . the trainer explains the labs . the learner completes the labs .
"""

# "Training": count which word follows which.
words = CORPUS.split()
next_counts = defaultdict(Counter)
for current, following in zip(words, words[1:]):
    next_counts[current][following] += 1


def predict(word):
    """Probability of each possible next word, learned purely by counting."""
    counts = next_counts[word]
    total = sum(counts.values())
    return {w: c / total for w, c in counts.most_common()}


def generate(start, length=12, seed=None):
    """'Inference': repeatedly sample the next word from the predicted probabilities."""
    rng = random.Random(seed)
    out = [start]
    for _ in range(length):
        probs = predict(out[-1])
        if not probs:
            break
        out.append(rng.choices(list(probs), weights=list(probs.values()))[0])
    return " ".join(out)


print("After 'the': ", {w: f"{p:.0%}" for w, p in predict("the").items()})
print("After 'labs':", {w: f"{p:.0%}" for w, p in predict("labs").items()})
print()
for seed in range(3):
    print("Generated:", generate("the", seed=seed))
