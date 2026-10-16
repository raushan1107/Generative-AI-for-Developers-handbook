"""Drill 05.3: same questions, different embedding settings. Does the best match change?
Run:  python lab05_03_models.py                    (your EMBED_MODEL, full size)
      python lab05_03_models.py --dims 256 1536    (text-embedding-3 models only: shortened vectors)
      python lab05_03_models.py --prefix           (nomic-embed-text: add its task prefixes)"""
import sys
import time
from pathlib import Path

import numpy as np

from embed import EMBED_MODEL, embed

ARTICLES = {p.stem: p.read_text(encoding="utf-8") for p in sorted((Path(__file__).parent / "data" / "help").glob("*.md"))}
QUESTIONS = {
    "Can I get my money back for a double charge?": "card-disputes",
    "Someone stole my wallet with my card in it": "lost-stolen-cards",
    "Why was I charged $29 last night?": "fees-and-charges",
    "The money I sent my landlord hasn't arrived": "transfers-and-payments",
    "I'm locked out of the app": "online-banking-access",
    "¿Qué pasa si saco el dinero de mi depósito a plazo antes?": "savings-and-cds",
}


def run(dims=None, prefix=False):
    q_texts = [("search_query: " if prefix else "") + q for q in QUESTIONS]
    d_texts = [("search_document: " if prefix else "") + t for t in ARTICLES.values()]
    start = time.perf_counter()
    docs, qs = embed(d_texts, dimensions=dims), embed(q_texts, dimensions=dims)
    took = time.perf_counter() - start
    docs /= np.linalg.norm(docs, axis=1, keepdims=True)
    qs /= np.linalg.norm(qs, axis=1, keepdims=True)
    scores = qs @ docs.T
    names = list(ARTICLES)
    correct = 0
    label = f"{EMBED_MODEL} dims={docs.shape[1]}{' +prefix' if prefix else ''}"
    print(f"\n{label}   ({took:.1f}s, cached calls are instant)")
    for (q, expected), row in zip(QUESTIONS.items(), scores):
        best = names[int(np.argmax(row))]
        correct += best == expected
        print(f"  {'OK ' if best == expected else 'MISS'} {row.max():.2f}  {q[:46]:<46} -> {best}")
    print(f"  {correct}/{len(QUESTIONS)} questions matched the right article")


if __name__ == "__main__":
    if "--dims" in sys.argv:
        for d in sys.argv[sys.argv.index("--dims") + 1:]:
            run(dims=int(d))
    else:
        run(prefix="--prefix" in sys.argv)
