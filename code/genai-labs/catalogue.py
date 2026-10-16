"""The RR Finance Bank product catalogue (fictional), used by Module 04 and 05 drills."""
import json
from pathlib import Path

PRODUCTS = json.loads((Path(__file__).parent / "data" / "products.json").read_text(encoding="utf-8"))
FIELDS = ("id", "name", "family", "audience", "annual_fee_usd", "rate_pct", "rate_type")


def find_products(family=None, audience=None, max_annual_fee_usd=None, text=None):
    """Plain keyword filter over the catalogue: the kind of function your app already has."""
    hits = []
    for p in PRODUCTS:
        if family and p["family"] != family:
            continue
        if audience and p["audience"] != audience:
            continue
        if max_annual_fee_usd is not None and p["annual_fee_usd"] > max_annual_fee_usd:
            continue
        if text and text.lower() not in (p["name"] + " " + p["description"]).lower():
            continue
        hits.append({k: p[k] for k in FIELDS})
    return hits


def get_product(product_id):
    return next((p for p in PRODUCTS if p["id"] == product_id.strip().upper()), None)
