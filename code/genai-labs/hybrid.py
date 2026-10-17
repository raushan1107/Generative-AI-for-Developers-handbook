"""Drill 05.9: hybrid search = keyword ranking (BM25) + vector ranking, merged with
Reciprocal Rank Fusion (RRF), the same merge Azure AI Search uses for hybrid queries."""
import re

import numpy as np
from rank_bm25 import BM25Okapi


STOP = set("a an and are as at be by can do does for from how i if in is it me my of on or our the there "
           "this to use we what when where which will with you your".split())


def tokenize(text):
    """A tiny analyzer: lowercase, keep codes like fr-12 together, drop filler words,
    and fold simple plurals (discounts -> discount). Search engines do this, and more, for you."""
    words = re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", text.lower())
    return [w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w
            for w in words if w not in STOP]


def bm25_ranking(query, documents):
    """Document indexes, best keyword match first (documents with no matching word are left out)."""
    bm25 = BM25Okapi([tokenize(d) for d in documents])
    scores = bm25.get_scores(tokenize(query))
    return [int(i) for i in np.argsort(-scores) if scores[i] > 0]


def vector_ranking(query_vector, doc_vectors):
    q = query_vector / np.linalg.norm(query_vector)
    d = doc_vectors / np.linalg.norm(doc_vectors, axis=1, keepdims=True)
    return [int(i) for i in np.argsort(-(d @ q))]


def rrf(rankings, k=60):
    """Each list gives a document 1/(k + rank). Add them up; highest total wins.
    Uses only positions, so BM25 scores and cosine scores never need to be comparable."""
    totals = {}
    for ranking in rankings:
        for rank, doc in enumerate(ranking, start=1):
            totals[doc] = totals.get(doc, 0.0) + 1.0 / (k + rank)
    return sorted(totals, key=lambda doc: -totals[doc])
