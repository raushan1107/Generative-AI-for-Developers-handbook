"""Drill 05.5, open alternative: the same catalogue in Chroma, a local vector database.
Run:  python lab05_05_chroma.py "make my app understand photos"
      python lab05_05_chroma.py "hands-on cloud course" --beginner-under 500"""
import sys

import chromadb

from catalogue import COURSES
from embed import embed

client = chromadb.PersistentClient(path="chroma_db")          # a folder on disk
courses = client.get_or_create_collection(name="courses", configuration={"hnsw": {"space": "cosine"}})

if courses.count() == 0:                                      # first run: load the catalogue
    texts = [f"{c['title']}. {c['description']}" for c in COURSES]
    courses.add(ids=[c["id"] for c in COURSES], embeddings=embed(texts).tolist(), documents=texts,
                metadatas=[{"level": c["level"], "format": c["format"], "price_usd": c["price_usd"]} for c in COURSES])

question = sys.argv[1] if len(sys.argv) > 1 else "make my app understand photos"
where = None
if "--beginner-under" in sys.argv:
    limit = int(sys.argv[sys.argv.index("--beginner-under") + 1])
    where = {"$and": [{"level": "beginner"}, {"price_usd": {"$lte": limit}}]}

res = courses.query(query_embeddings=embed([question]).tolist(), n_results=3, where=where)
print(f"{question!r}" + (f"  where={where}" if where else ""))
for cid, dist, meta, doc in zip(res["ids"][0], res["distances"][0], res["metadatas"][0], res["documents"][0]):
    print(f"  distance {dist:.3f}  {cid}  {doc.split('.')[0]}  ({meta['level']}, ${meta['price_usd']})")
