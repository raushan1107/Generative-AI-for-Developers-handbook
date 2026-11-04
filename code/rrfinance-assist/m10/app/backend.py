"""Stand-in for RR Finance Bank's real systems (products, accounts, cards, transactions). Fictional data.
In a real bank these are existing APIs or core-banking systems; the assistant only calls them through tools.
Dates are relative to today so the demo always has recent and older payments."""
import json
from datetime import date, timedelta
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
PRODUCTS = {p["id"]: p for p in json.loads((DATA / "products.json").read_text(encoding="utf-8"))}


def _day(offset: int) -> str:
    return (date.today() + timedelta(days=offset)).isoformat()


CUSTOMERS = {
    "RR-10293": {"name": "Mei Chen", "email": "mei@example.com"},
    "RR-20877": {"name": "Diego Alvarez", "email": "diego@example.com"},
    "RR-31002": {"name": "Asha Nair", "email": "asha@example.com"},
}

ACCOUNTS = {
    "AC-5512": {"customer_id": "RR-10293", "product_id": "P101", "balance_usd": 1840.22, "courtesy_refund_used": False},
    "AC-6630": {"customer_id": "RR-20877", "product_id": "P103", "balance_usd": 31250.00, "courtesy_refund_used": False},
    "AC-7720": {"customer_id": "RR-20877", "product_id": "P104", "balance_usd": 48250.00, "courtesy_refund_used": False},
    "AC-8801": {"customer_id": "RR-31002", "product_id": "P102", "balance_usd": 212.40, "courtesy_refund_used": True},
}

CARDS = {
    "4821": {"customer_id": "RR-10293", "product_id": "P110", "status": "active"},
    "1177": {"customer_id": "RR-10293", "product_id": "P101", "status": "replacement_sent",
             "replacement": {"sent_on": _day(-3), "arrives_by": _day(4), "express": False}},
    "9034": {"customer_id": "RR-20877", "product_id": "P111", "status": "active"},
    "5560": {"customer_id": "RR-31002", "product_id": "P102", "status": "frozen"},
}

# Payments on cards, and the account's overdraft days (what the fee refund quote needs).
TRANSACTIONS = {
    "TX-1001": {"card": "4821", "date": _day(-37), "merchant": "SkyHigh Airlines TKT 0172", "amount_usd": 412.00},
    "TX-1002": {"card": "4821", "date": _day(-37), "merchant": "SkyHigh Airlines TKT 0172", "amount_usd": 412.00},
    "TX-1003": {"card": "4821", "date": _day(-34), "merchant": "Northside Pharmacy", "amount_usd": 18.40},
    "TX-1006": {"card": "4821", "date": _day(-75), "merchant": "Harbor Hotel", "amount_usd": 260.00},
    "TX-2001": {"card": "9034", "date": _day(-6), "merchant": "QuickFix Electronics", "amount_usd": 899.00},
    "TX-2002": {"card": "9034", "date": _day(-12), "merchant": "Tokyo Ramen House", "amount_usd": 31.50},
    "TX-3001": {"card": "5560", "date": _day(-3), "merchant": "Campus Bookshop", "amount_usd": 46.80},
}
OVERDRAFT_DAYS = {   # account -> days it ended overdrawn, with the $29 fees the bank charged that day
    "AC-5512": [{"date": _day(-12), "end_of_day_balance_usd": -212.00, "fees_charged": 4},
                {"date": _day(-11), "end_of_day_balance_usd": -31.00, "fees_charged": 1}],
    "AC-8801": [{"date": _day(-20), "end_of_day_balance_usd": -80.00, "fees_charged": 1}],
}


def accounts_of(customer_id: str) -> list[dict]:
    return [{"account_id": aid, "product": PRODUCTS[a["product_id"]]["name"], "balance_usd": a["balance_usd"]}
            for aid, a in ACCOUNTS.items() if a["customer_id"] == customer_id]


def cards_of(customer_id: str) -> list[dict]:
    return [{"card_last4": last4, "product": PRODUCTS[c["product_id"]]["name"], "status": c["status"]}
            for last4, c in CARDS.items() if c["customer_id"] == customer_id]


# ---------------------------------------------------------------- milestone 7: things that can change
# Card freezes and disputes. Writes go through the two functions below, which re-check the rules,
# are idempotent (same key, same result, done once) and are logged for audit.
DISPUTES: dict[str, dict] = {}          # txn_id -> dispute
ACTIONS_FILE = DATA / "actions.jsonl"
_DONE: dict[str, dict] = {}


class ActionError(Exception):
    """A rule says no. The message is safe to show to the customer."""


def _log(action: str, record: dict):
    ACTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with ACTIONS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"action": action, "at": date.today().isoformat(), **record}) + "\n")


def freeze_card(card_last4: str, key: str) -> dict:
    if key in _DONE:                                     # a retry of an action already done: same answer
        return _DONE[key]
    card = CARDS.get(card_last4)
    if card is None:
        raise ActionError("This card doesn't exist.")
    if card["status"] == "frozen":
        raise ActionError("This card is already frozen.")
    card["status"] = "frozen"
    _DONE[key] = result = {"card_last4": card_last4, "status": "frozen"}
    _log("freeze_card", {"key": key, **result})
    return result


def open_dispute(txn_id: str, reason: str, provisional_credit_by: str, key: str) -> dict:
    if key in _DONE:
        return _DONE[key]
    if txn_id in DISPUTES:
        raise ActionError(f"{txn_id} is already being disputed ({DISPUTES[txn_id]['dispute_id']}).")
    t = TRANSACTIONS[txn_id]
    dispute = {"dispute_id": "DSP-" + key[-6:], "txn_id": txn_id, "amount_usd": t["amount_usd"], "reason": reason,
               "provisional_credit_by": provisional_credit_by}
    DISPUTES[txn_id] = dispute
    _DONE[key] = dispute
    _log("open_dispute", {"key": key, **dispute})
    return dispute
