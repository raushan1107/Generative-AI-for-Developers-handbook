"""Drill 05.1: your first embeddings. Text in, a long list of numbers out."""
import numpy as np

from embed import EMBED_MODEL
from llm import get_client

texts = [
    "How do I dispute a double charge?",
    "Can I have my money back for a wrong payment?",
    "My card was stolen.",
]

client = get_client()
response = client.embeddings.create(model=EMBED_MODEL, input=texts)   # one call, a batch of texts

print("model:", EMBED_MODEL, "| tokens used:", response.usage.prompt_tokens)
for text, item in zip(texts, response.data):
    v = np.array(item.embedding)
    print(f"\n{text}")
    print(f"  dimensions: {len(v)}   length (norm): {np.linalg.norm(v):.3f}")
    print(f"  first 5 numbers: {np.round(v[:5], 4).tolist()}")
