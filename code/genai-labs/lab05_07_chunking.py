"""Drill 05.7: which chunking strategy finds the answer most often?
For each question we know the article and a phrase the retrieved chunk must contain."""
import json
from pathlib import Path

import numpy as np

from chunkers import STRATEGIES, load_articles
from embed import embed

QUESTIONS = json.loads((Path(__file__).parent / "data" / "help_questions.json").read_text(encoding="utf-8"))
articles = load_articles()
q_vectors = embed([q["question"] for q in QUESTIONS])
q_vectors /= np.linalg.norm(q_vectors, axis=1, keepdims=True)

print(f"{'strategy':<17}{'chunks':>7}{'avg chars':>10}{'hit@1':>7}{'hit@3':>7}")
for name, chunker in STRATEGIES.items():
    chunks = [(source, text) for source, md in articles.items() for text in chunker(md)]
    vectors = embed([text for _, text in chunks])
    vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)
    hit1 = hit3 = 0
    misses = []
    for q, row in zip(QUESTIONS, q_vectors @ vectors.T):
        top = np.argsort(-row)[:3]
        found = [chunks[i][0] == q["source"] and q["must_contain"] in chunks[i][1] for i in top]
        hit1 += found[0]
        hit3 += any(found)
        if not any(found):
            misses.append(q["question"])
    avg = sum(len(t) for _, t in chunks) / len(chunks)
    print(f"{name:<17}{len(chunks):>7}{avg:>10.0f}{hit1:>4}/{len(QUESTIONS)}{hit3:>4}/{len(QUESTIONS)}")
    for m in misses:
        print(f"{'':<6}missed: {m}")
