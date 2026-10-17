"""Lab 2, Exercise 3: embeddings turn text into vectors; similar meanings get similar vectors.
Run:  python l2_embeddings.py"""
import numpy as np

from client import EMBED_MODEL, get_embed_client

TEXTS = [
    "How do I get my money back?",
    "Can I dispute a double charge?",
    "¿Cómo reclamo un cargo?",
    "My card was stolen",
    "Someone took my wallet",
    "What's the weather in Paris?",
]
response = get_embed_client().embeddings.create(model=EMBED_MODEL, input=TEXTS)
vectors = np.array([d.embedding for d in response.data])
vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)          # length 1: dot product = cosine similarity
print(f"{len(TEXTS)} texts -> vectors of {vectors.shape[1]} numbers. First five of the first: "
      f"{np.round(vectors[0][:5], 3).tolist()}\n")

similarity = vectors @ vectors.T
for i, text in enumerate(TEXTS):
    j = max((k for k in range(len(TEXTS)) if k != i), key=lambda k: similarity[i, k])
    print(f"{text:38} closest: {TEXTS[j]:38} ({similarity[i, j]:.2f})")
