"""Drill 05.6: keyword search vs semantic search over the course catalogue.
The learner's words rarely match the words on your course pages."""
import re

import numpy as np

from catalogue import COURSES
from embed import embed

STOP = set("a an and the to for of in on my me i i'm im want is it with how do can at be what".split())
QUERIES = [
    "I want my app to recognise objects in photos",
    "cheap intro to containers",
    "not a coder, want to use chat assistants better at work",
    "get certified as a cloud admin",
    "make answers come from our own documents",
]


def words(text):
    return {w for w in re.findall(r"[a-z0-9-]+", text.lower()) if w not in STOP}


def keyword_top(query):
    """Count shared words between the query and each course: what a basic search box does."""
    q = words(query)
    scores = [len(q & words(c["title"] + " " + c["description"])) for c in COURSES]
    best = int(np.argmax(scores))
    return (COURSES[best]["title"], scores[best]) if scores[best] else ("(no match)", 0)


texts = [f"{c['title']}. {c['description']}" for c in COURSES]
docs = embed(texts)
docs /= np.linalg.norm(docs, axis=1, keepdims=True)
qs = embed(QUERIES)
qs /= np.linalg.norm(qs, axis=1, keepdims=True)

for query, row in zip(QUERIES, qs @ docs.T):
    title, overlap = keyword_top(query)
    best = int(np.argmax(row))
    print(f"\n{query}")
    print(f"  keyword : {title}  ({overlap} shared words)")
    print(f"  semantic: {COURSES[best]['title']}  (cosine {row[best]:.2f})")
