"""Drill 05.8: metadata filters. Filter BEFORE ranking (pre-filter) or AFTER (post-filter)?"""
from catalogue import PRODUCTS
from embed import embed
from vector_store import VectorStore, matches

store = VectorStore()
texts = [f"{p['name']}. {p['description']}" for p in PRODUCTS]
store.add(ids=[p["id"] for p in PRODUCTS], vectors=embed(texts), texts=[p["name"] for p in PRODUCTS],
          metadatas=[{"family": p["family"], "audience": p["audience"], "annual_fee_usd": p["annual_fee_usd"]}
                     for p in PRODUCTS])

query = "earn rewards when I travel and spend abroad"
where = {"family": "cards", "annual_fee_usd": {"$lte": 0}}
q = embed([query])[0]


def show(title, hits):
    print(title)
    for h in hits:
        m = h["metadata"]
        print(f"  {h['score']:.2f}  {h['id']}  {h['text']:<28} {m['family']:<9} ${m['annual_fee_usd']} a year")
    if not hits:
        print("  (nothing left)")


print(f"query: {query!r}\nfilter: {where}\n")
show("No filter, top 3:", store.search(q, k=3))
show("\nPost-filter (top 3 first, then filter):", [h for h in store.search(q, k=3) if matches(h["metadata"], where)])
show("\nPre-filter (filter first, then top 3):", store.search(q, k=3, where=where))
