from app.llm import get_client
from app.search import SearchService
from app import backend

s = SearchService(get_client())
Q = [("a card I can use on holiday without extra charges", "product", {}),
     ("save for a house deposit", "product", {}),
     ("someone is asking me to move money to a safe account", "help", {}),
     ("I paid the wrong person", "help", {}),
     ("card for spending abroad, no annual fee", "product", {"family": "cards", "max_annual_fee_usd": 0})]
for q, kind, f in Q:
    hits = s.search(q, k=3, kind=kind, **f)
    label = f"{q} ({kind}{', ' + ', '.join(f'{k}={v}' for k, v in f.items()) if f else ''})"
    if kind == "product":
        r = ", ".join(f"{h['id']} {h['title']} (${backend.PRODUCTS[h['id']]['annual_fee_usd']})" for h in hits)
    else:
        r = ", ".join(f"{h['id']} \"{h['title'].split(' › ')[-1]}\"" for h in hits)
    print(f"{label}\n  -> {r}")
