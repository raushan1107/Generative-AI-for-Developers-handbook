"""Semantic and hybrid search over the course catalogue and help-centre articles (milestone 5).

Two backends with the same interface:
- LocalIndex: vectors in a numpy file plus BM25 keywords, merged with RRF. No cloud needed.
- AzureIndex: Azure AI Search, which does keyword + vector + RRF on the service.
Build the index first:  python -m scripts.build_index"""
import json
import re
from pathlib import Path

import numpy as np
from rank_bm25 import BM25Okapi

from app import backend
from app.config import (AZURE_SEARCH_API_KEY, AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_INDEX, EMBED_MODEL, INDEX_DIR,
                        SEARCH_BACKEND)

HELP_DIR = Path(__file__).resolve().parent.parent / "data" / "help"
STOP = set("a an and are as at be by can do does for from how i if in is it me my of on or our the there "
           "this to use we what when where which will with you your".split())


# ---------------------------------------------------------------- documents
def chunk_by_headings(markdown: str):
    """One chunk per '## ' section, prefixed with 'Article > Section' so it stands on its own.
    Drill 05.7 showed this beat fixed-size chunks on our help centre."""
    title = re.search(r"^# (.+)$", markdown, re.M).group(1).strip()
    for part in re.split(r"^## ", markdown, flags=re.M)[1:]:
        heading, _, body = part.partition("\n")
        yield heading.strip(), f"{title} > {heading.strip()}\n{body.strip()}"


def load_documents():
    """Everything we search, as plain dicts: one per course and one per help-article section."""
    docs = []
    for c in backend.COURSES.values():
        docs.append({"id": c["id"], "kind": "course", "title": c["title"],
                     "text": f"{c['title']}. {c['description']}",
                     "level": c["level"], "format": c["format"], "price_usd": c["price_usd"]})
    for path in sorted(HELP_DIR.glob("*.md")):
        for n, (heading, text) in enumerate(chunk_by_headings(path.read_text(encoding="utf-8")), 1):
            docs.append({"id": f"{path.stem}-{n}", "kind": "help", "title": heading, "text": text,
                         "source": f"{path.stem}.md", "level": None, "format": None, "price_usd": None})
    return docs


def embed(client, texts, batch=64) -> np.ndarray:
    vectors = []
    for i in range(0, len(texts), batch):
        response = client.embeddings.create(model=EMBED_MODEL, input=texts[i:i + batch])
        vectors += [d.embedding for d in response.data]
    v = np.array(vectors, dtype=np.float32)
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def tokenize(text: str):
    words = re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", text.lower())
    return [w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w
            for w in words if w not in STOP]


def rrf(rankings, k=60):
    totals = {}
    for ranking in rankings:
        for rank, i in enumerate(ranking, start=1):
            totals[i] = totals.get(i, 0.0) + 1.0 / (k + rank)
    return sorted(totals.items(), key=lambda kv: -kv[1])


def _matches(doc, filters):
    if filters.get("kind") and doc["kind"] != filters["kind"]:
        return False
    if filters.get("level") and doc["level"] != filters["level"]:
        return False
    if filters.get("format") and doc["format"] != filters["format"]:
        return False
    if filters.get("max_price_usd") is not None and (doc["price_usd"] is None or doc["price_usd"] > filters["max_price_usd"]):
        return False
    return True


# ---------------------------------------------------------------- local backend
class LocalIndex:
    def __init__(self, docs, vectors, model):
        self.docs, self.vectors, self.model = docs, vectors, model
        self.bm25 = BM25Okapi([tokenize(d["text"]) for d in docs])

    @classmethod
    def build(cls, client):
        docs = load_documents()
        return cls(docs, embed(client, [d["text"] for d in docs]), EMBED_MODEL)

    def save(self, folder=INDEX_DIR):
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        np.save(folder / "vectors.npy", self.vectors)
        (folder / "docs.json").write_text(json.dumps({"model": self.model, "docs": self.docs}, ensure_ascii=False),
                                          encoding="utf-8")

    @classmethod
    def load(cls, folder=INDEX_DIR):
        folder = Path(folder)
        saved = json.loads((folder / "docs.json").read_text(encoding="utf-8"))
        if saved["model"] != EMBED_MODEL:      # vectors from different models can't be compared
            raise RuntimeError(f"index was built with {saved['model']}, but EMBED_MODEL is {EMBED_MODEL}; rebuild it")
        return cls(saved["docs"], np.load(folder / "vectors.npy"), saved["model"])

    def search(self, query, query_vector, k=5, **filters):
        allowed = [i for i, d in enumerate(self.docs) if _matches(d, filters)]     # pre-filter
        if not allowed:
            return []
        cosine = self.vectors[allowed] @ query_vector
        vector_rank = [allowed[j] for j in np.argsort(-cosine)]
        keyword_scores = self.bm25.get_scores(tokenize(query))
        keyword_rank = sorted((i for i in allowed if keyword_scores[i] > 0), key=lambda i: -keyword_scores[i])
        cos_of = dict(zip(allowed, cosine))
        return [{**self.docs[i], "score": round(score, 4), "cosine": round(float(cos_of[i]), 3)}
                for i, score in rrf([keyword_rank, vector_rank])[:k]]


# ---------------------------------------------------------------- Azure AI Search backend
class AzureIndex:
    """Same search() as LocalIndex, done by Azure AI Search (hybrid = keyword + vector, merged with RRF)."""
    def __init__(self):
        from azure.core.credentials import AzureKeyCredential
        from azure.search.documents import SearchClient
        self.client = SearchClient(AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_INDEX, AzureKeyCredential(AZURE_SEARCH_API_KEY))

    def search(self, query, query_vector, k=5, **filters):
        from azure.search.documents.models import VectorizedQuery
        clauses = []
        for field in ("kind", "level", "format"):
            if filters.get(field):
                clauses.append(f"{field} eq '{filters[field]}'")          # values come from enums, not free text
        if filters.get("max_price_usd") is not None:
            clauses.append(f"price_usd le {int(filters['max_price_usd'])}")
        results = self.client.search(
            search_text=query, top=k, filter=" and ".join(clauses) or None,
            vector_queries=[VectorizedQuery(vector=query_vector.tolist(), k_nearest_neighbors=k, fields="contentVector")])
        return [{**{key: r.get(key) for key in ("id", "kind", "title", "text", "source", "level", "format", "price_usd")},
                 "score": round(r["@search.score"], 4)} for r in results]


# ---------------------------------------------------------------- the service the app uses
class SearchService:
    def __init__(self, client, index=None):
        self.client = client
        if index is not None:
            self.index = index
        elif SEARCH_BACKEND == "azure":
            self.index = AzureIndex()
        else:
            self.index = LocalIndex.load()

    def search(self, query: str, k: int = 5, **filters):
        query_vector = embed(self.client, [query])[0]
        return self.index.search(query, query_vector, k=k, **filters)
