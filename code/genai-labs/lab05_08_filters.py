"""Drill 05.8: metadata filters. Filter BEFORE ranking (pre-filter) or AFTER (post-filter)?"""
from catalogue import COURSES
from embed import embed
from vector_store import VectorStore, matches

store = VectorStore()
texts = [f"{c['title']}. {c['description']}" for c in COURSES]
store.add(ids=[c["id"] for c in COURSES], vectors=embed(texts), texts=[c["title"] for c in COURSES],
          metadatas=[{"level": c["level"], "format": c["format"], "price_usd": c["price_usd"]} for c in COURSES])

query = "hands-on course about AI and language models"
where = {"level": "beginner", "price_usd": {"$lte": 500}}
q = embed([query])[0]


def show(title, hits):
    print(title)
    for h in hits:
        m = h["metadata"]
        print(f"  {h['score']:.2f}  {h['id']}  {h['text']:<40} {m['level']:<13} ${m['price_usd']}")
    if not hits:
        print("  (nothing left)")


print(f"query: {query!r}\nfilter: {where}\n")
show("No filter, top 3:", store.search(q, k=3))
show("\nPost-filter (top 3 first, then filter):", [h for h in store.search(q, k=3) if matches(h["metadata"], where)])
show("\nPre-filter (filter first, then top 3):", store.search(q, k=3, where=where))
