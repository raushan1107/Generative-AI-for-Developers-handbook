"""Lab 2, Exercise 4: a semantic search application over RR Finance Bank's help centre.
Index: split each article by heading (keeping its introduction), embed every section once and save it.
Search: embed the question, rank by meaning (cosine) and by keywords (BM25), merge the two rankings (RRF).
Run:  python l2_search.py "money back if I paid the wrong person" """
import json
import re
import sys
from pathlib import Path

import numpy as np
from rank_bm25 import BM25Okapi

from client import EMBED_MODEL, get_embed_client

HELP = Path(__file__).parent / "data" / "help"
INDEX = Path(__file__).parent / "data" / "search_index.json"


def sections():
    for path in sorted(HELP.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        title = re.search(r"^# (.+)$", text, re.M).group(1)
        intro, *parts = re.split(r"^## ", re.sub(r"^# .+\n", "", text, count=1), flags=re.M)
        pieces = ([("Overview", intro)] if intro.strip() else []) + [p.partition("\n")[::2] for p in parts]
        for heading, body in pieces:
            yield {"source": path.name, "title": f"{title} > {heading.strip()}",
                   "text": f"{title} > {heading.strip()}\n{body.strip()}"}


def embed(texts):
    data = get_embed_client().embeddings.create(model=EMBED_MODEL, input=texts).data
    v = np.array([d.embedding for d in data])
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def load_index():
    """Build the index the first time (a few seconds), then reuse it."""
    if INDEX.exists():
        saved = json.loads(INDEX.read_text(encoding="utf-8"))
        if saved["model"] == EMBED_MODEL:                    # vectors from another model can't be compared
            return saved["docs"], np.array(saved["vectors"])
    docs = list(sections())
    vectors = embed([d["text"] for d in docs])
    INDEX.write_text(json.dumps({"model": EMBED_MODEL, "docs": docs, "vectors": vectors.tolist()}), encoding="utf-8")
    print(f"(indexed {len(docs)} help sections with {EMBED_MODEL})")
    return docs, vectors


def words(text):
    """A tiny analyzer: lower-case, keep codes like fr-12 whole, fold simple plurals (payments -> payment)."""
    found = re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", text.lower())
    return [w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w for w in found]


def search(query, docs, vectors, k=3):
    cosine = vectors @ embed([query])[0]
    by_meaning = list(np.argsort(-cosine))
    keyword_scores = BM25Okapi([words(d["text"]) for d in docs]).get_scores(words(query))
    by_keyword = [i for i in np.argsort(-keyword_scores) if keyword_scores[i] > 0]
    rrf = {}
    for ranking in (by_meaning, by_keyword):
        for rank, i in enumerate(ranking, start=1):
            rrf[i] = rrf.get(i, 0) + 1 / (60 + rank)
    best = sorted(rrf, key=lambda i: -rrf[i])[:k]
    return [(docs[i], float(cosine[i])) for i in best]


if __name__ == "__main__":
    docs, vectors = load_index()
    queries = sys.argv[1:] or ["money back if I paid the wrong person", "Instant Pay", "safe account", "fingerprint sign in"]
    for q in queries:
        print(f"\n{q}")
        for doc, score in search(q, docs, vectors):
            print(f"  {score:.2f}  {doc['title']}")
