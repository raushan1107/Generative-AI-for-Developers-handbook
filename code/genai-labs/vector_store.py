"""Drill 05.4 reference solution: a tiny in-memory vector store (about 60 lines).
Good enough for a few thousand items; a vector database adds indexes (HNSW), scale,
persistence, security and filtering at speed. The ideas are the same."""
import json
from pathlib import Path

import numpy as np

OPS = {"$eq": lambda a, b: a == b, "$ne": lambda a, b: a != b, "$lt": lambda a, b: a < b,
       "$lte": lambda a, b: a <= b, "$gt": lambda a, b: a > b, "$gte": lambda a, b: a >= b,
       "$in": lambda a, b: a in b}


def matches(metadata: dict, where: dict | None) -> bool:
    """where={"level": "beginner", "price_usd": {"$lte": 500}}: every condition must hold."""
    for field, cond in (where or {}).items():
        value = metadata.get(field)
        conditions = cond if isinstance(cond, dict) else {"$eq": cond}
        for op, expected in conditions.items():
            if value is None or not OPS[op](value, expected):
                return False
    return True


class VectorStore:
    def __init__(self):
        self.ids, self.texts, self.metadatas = [], [], []
        self.vectors = np.zeros((0, 0), dtype=np.float32)

    def add(self, ids, vectors, texts, metadatas=None):
        v = np.asarray(vectors, dtype=np.float32)
        v = v / np.linalg.norm(v, axis=1, keepdims=True)     # unit length: dot product == cosine
        self.vectors = v if self.vectors.size == 0 else np.vstack([self.vectors, v])
        self.ids += list(ids)
        self.texts += list(texts)
        self.metadatas += list(metadatas or [{} for _ in ids])

    def search(self, query_vector, k=3, where=None):
        """Top-k by cosine similarity among items whose metadata matches `where` (pre-filtering)."""
        if not self.ids:
            return []
        q = np.asarray(query_vector, dtype=np.float32)
        scores = self.vectors @ (q / np.linalg.norm(q))
        allowed = [i for i in range(len(self.ids)) if matches(self.metadatas[i], where)]
        best = sorted(allowed, key=lambda i: -scores[i])[:k]
        return [{"id": self.ids[i], "score": round(float(scores[i]), 4), "text": self.texts[i],
                 "metadata": self.metadatas[i]} for i in best]

    def save(self, folder):
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        np.save(folder / "vectors.npy", self.vectors)
        (folder / "items.json").write_text(json.dumps(
            {"ids": self.ids, "texts": self.texts, "metadatas": self.metadatas}, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, folder):
        folder, store = Path(folder), cls()
        store.vectors = np.load(folder / "vectors.npy")
        items = json.loads((folder / "items.json").read_text(encoding="utf-8"))
        store.ids, store.texts, store.metadatas = items["ids"], items["texts"], items["metadatas"]
        return store
