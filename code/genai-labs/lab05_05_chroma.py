"""Drill 05.5, open alternative: the same catalogue in Chroma, a local vector database.
Run:  python lab05_05_chroma.py "somewhere to save for a house deposit"
      python lab05_05_chroma.py "card for spending abroad" --cards-under 100"""
import sys

import chromadb

from catalogue import PRODUCTS
from embed import embed

client = chromadb.PersistentClient(path="chroma_db")          # a folder on disk
products = client.get_or_create_collection(name="products", metadata={"hnsw:space": "cosine"})   # cosine distance

if products.count() == 0:                                     # first run: load the catalogue
    texts = [f"{p['name']}. {p['description']}" for p in PRODUCTS]
    products.add(ids=[p["id"] for p in PRODUCTS], embeddings=embed(texts).tolist(), documents=texts,
                 metadatas=[{"family": p["family"], "audience": p["audience"], "annual_fee_usd": p["annual_fee_usd"]}
                            for p in PRODUCTS])

question = sys.argv[1] if len(sys.argv) > 1 else "somewhere to save for a house deposit"
where = None
if "--cards-under" in sys.argv:
    limit = int(sys.argv[sys.argv.index("--cards-under") + 1])
    where = {"$and": [{"family": "cards"}, {"annual_fee_usd": {"$lte": limit}}]}

res = products.query(query_embeddings=embed([question]).tolist(), n_results=3, where=where)
print(f"{question!r}" + (f"  where={where}" if where else ""))
for pid, dist, meta, doc in zip(res["ids"][0], res["distances"][0], res["metadatas"][0], res["documents"][0]):
    print(f"  distance {dist:.3f}  {pid}  {doc.split('.')[0]}  ({meta['family']}, ${meta['annual_fee_usd']} a year)")
