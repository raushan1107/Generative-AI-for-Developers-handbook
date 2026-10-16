"""Drill 05.6: keyword search vs semantic search over the product catalogue.
The customer's words rarely match the words on your product pages."""
import re

import numpy as np

from catalogue import PRODUCTS
from embed import embed

STOP = set("a an and the to for of in on my me i i'm im want is it with how do can at be what".split())
QUERIES = [
    "I want to stop paying so much interest on my credit card debt",
    "a card I can use on holiday without extra charges",
    "somewhere safe for my rainy-day money that grows",
    "first bank account for my 19-year-old at university",
    "buy my first flat",
]


def words(text):
    return {w for w in re.findall(r"[a-z0-9-]+", text.lower()) if w not in STOP}


def keyword_top(query):
    """Count shared words between the query and each product: what a basic search box does."""
    q = words(query)
    scores = [len(q & words(p["name"] + " " + p["description"])) for p in PRODUCTS]
    best = int(np.argmax(scores))
    return (PRODUCTS[best]["name"], scores[best]) if scores[best] else ("(no match)", 0)


texts = [f"{p['name']}. {p['description']}" for p in PRODUCTS]
docs = embed(texts)
docs /= np.linalg.norm(docs, axis=1, keepdims=True)
qs = embed(QUERIES)
qs /= np.linalg.norm(qs, axis=1, keepdims=True)

for query, row in zip(QUERIES, qs @ docs.T):
    title, overlap = keyword_top(query)
    best = int(np.argmax(row))
    print(f"\n{query}")
    print(f"  keyword : {title}  ({overlap} shared words)")
    print(f"  semantic: {PRODUCTS[best]['name']}  (cosine {row[best]:.2f})")
