"""Module 05 helper: turn texts into embedding vectors, in batches, with a small disk cache
so re-running a drill doesn't pay for the same embeddings twice."""
import hashlib
import json
import os
from pathlib import Path

import numpy as np

from llm import PROVIDER, get_client

# The embedding model. On Azure, the DEPLOYMENT name of an embedding model (add it to .env).
EMBED_MODEL = {
    "azure": os.getenv("AZURE_OPENAI_EMBED_DEPLOYMENT", "embed"),
    "openai": os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small"),
    "ollama": os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"),
}.get(PROVIDER, "")

CACHE_FILE = Path(__file__).parent / "data" / ".embed_cache.json"
BATCH = 64
_cache = json.loads(CACHE_FILE.read_text(encoding="utf-8")) if CACHE_FILE.exists() else {}
_client = None


def _key(model, dimensions, text):
    return hashlib.sha1(f"{model}|{dimensions}|{text}".encode("utf-8")).hexdigest()


def embed(texts, model=EMBED_MODEL, dimensions=None) -> np.ndarray:
    """Return an array of shape (len(texts), dims). `dimensions` works with text-embedding-3 models."""
    global _client
    keys = [_key(model, dimensions, t) for t in texts]
    todo = [(k, t) for k, t in zip(keys, texts) if k not in _cache]
    if todo:
        _client = _client or get_client()
        extra = {"dimensions": dimensions} if dimensions else {}
        for i in range(0, len(todo), BATCH):
            batch = todo[i:i + BATCH]
            response = _client.embeddings.create(model=model, input=[t for _, t in batch], **extra)
            for (k, _), item in zip(batch, response.data):
                _cache[k] = item.embedding
        CACHE_FILE.write_text(json.dumps(_cache), encoding="utf-8")
    return np.array([_cache[k] for k in keys], dtype=np.float32)
