"""Module 06 helper: the knowledge index (embedding generation + vector storage).
Embeds chunks in batches, re-embeds only chunks whose text changed, stores each vector with its
text and metadata, and records how the index was built, so a mismatch fails loudly instead of
returning nonsense. Search is hybrid (BM25 + vectors, merged with RRF) with an audience pre-filter."""
import hashlib
import json
import time
from pathlib import Path

import numpy as np

from embed import EMBED_MODEL, embed
from hybrid import bm25_ranking, rrf
from rag_chunks import CHUNKER_VERSION

INDEX_DIR = Path(__file__).parent / "data" / "kb_index"


def text_hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def unit(v: np.ndarray) -> np.ndarray:
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


class KnowledgeIndex:
    def __init__(self, chunks, vectors, manifest):
        self.chunks, self.vectors, self.manifest = chunks, vectors, manifest

    @classmethod
    def build(cls, chunks, previous=None):
        """Return (index, stats). Vectors of unchanged chunks are reused from `previous`,
        but only if it was built with the same embedding model and chunker."""
        reusable = {}
        if previous and previous.manifest["embed_model"] == EMBED_MODEL \
                and previous.manifest["chunker"] == CHUNKER_VERSION:
            reusable = {c["id"]: (c["hash"], previous.vectors[i]) for i, c in enumerate(previous.chunks)}
        chunks = [c | {"hash": text_hash(c["text"])} for c in chunks]
        stats = {"new": 0, "changed": 0, "unchanged": 0, "removed": len(set(reusable) - {c["id"] for c in chunks})}
        vectors, todo = [None] * len(chunks), []
        for i, c in enumerate(chunks):
            old = reusable.get(c["id"])
            if old and old[0] == c["hash"]:
                vectors[i] = old[1]
                stats["unchanged"] += 1
            else:
                todo.append(i)
                stats["changed" if old else "new"] += 1
        if todo:                                           # one batched call per 64 texts (see embed.py)
            for i, v in zip(todo, unit(embed([chunks[i]["text"] for i in todo]))):
                vectors[i] = v
        matrix = np.array(vectors, dtype=np.float32)
        manifest = {"embed_model": EMBED_MODEL, "dimensions": int(matrix.shape[1]), "chunker": CHUNKER_VERSION,
                    "chunks": len(chunks), "built": time.strftime("%Y-%m-%d %H:%M:%S")}
        return cls(chunks, matrix, manifest), stats

    def save(self, folder=INDEX_DIR):
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        np.save(folder / "vectors.npy", self.vectors)
        (folder / "chunks.json").write_text(json.dumps(self.chunks, ensure_ascii=False, indent=1), encoding="utf-8")
        (folder / "manifest.json").write_text(json.dumps(self.manifest, indent=1), encoding="utf-8")

    @classmethod
    def load(cls, folder=INDEX_DIR, check_model=True):
        folder = Path(folder)
        manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
        if check_model and manifest["embed_model"] != EMBED_MODEL:
            raise RuntimeError(f"index built with {manifest['embed_model']}, but EMBED_MODEL is {EMBED_MODEL}: rebuild it")
        chunks = json.loads((folder / "chunks.json").read_text(encoding="utf-8"))
        return cls(chunks, np.load(folder / "vectors.npy"), manifest)

    def search(self, query, k=4, audience=("public",), min_score=None):
        """Top k chunks the audience may see, best first. Each hit has 'score' (cosine with the query).
        With min_score, chunks below it are dropped, so an off-topic question can return nothing."""
        allowed = [i for i, c in enumerate(self.chunks) if c["audience"] in audience]   # permission pre-filter
        if not allowed:
            return []
        cosine = self.vectors[allowed] @ unit(embed([query])[0])
        vector_rank = [allowed[j] for j in np.argsort(-cosine)]
        keyword_rank = [allowed[j] for j in bm25_ranking(query, [self.chunks[i]["text"] for i in allowed])]
        score_of = dict(zip(allowed, cosine.tolist()))
        hits = [self.chunks[i] | {"score": round(score_of[i], 3)} for i in rrf([keyword_rank, vector_rank])]
        if min_score is not None:
            hits = [h for h in hits if h["score"] >= min_score]
        return hits[:k]


def load_or_build():
    """The index the later drills use. Built from the knowledge base on first use, then loaded."""
    try:
        return KnowledgeIndex.load()
    except FileNotFoundError:
        from ingest import load_knowledge_base
        from rag_chunks import chunk_all
        index, _ = KnowledgeIndex.build(chunk_all(load_knowledge_base()))
        index.save()
        return index
