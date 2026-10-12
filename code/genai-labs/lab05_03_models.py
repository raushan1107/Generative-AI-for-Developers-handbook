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
    "Can I get my money back if I cancel next week?": "refunds-and-cancellations",
    "The sandbox won't start, what do I do?": "labs-and-sandboxes",
    "My certificate has a typo in my surname": "certificates",
    "Can my company pay in three parts?": "payments-and-invoices",
    "Do you offer captions for deaf learners?": "accessibility",
    "¿Cuánto tiempo es válido mi voucher de examen?": "exam-vouchers",
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
