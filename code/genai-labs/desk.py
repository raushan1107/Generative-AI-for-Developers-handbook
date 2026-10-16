"""Module 07: stand-in RR Finance Bank systems for the agent drills (fictional, in memory).
Read functions look things up; write functions change state and are recorded in ACTIONS.
Dates are relative to today, so there are always recent and older payments.
Errors are DeskError with a message an agent can act on ("call my_cards to get the right card")."""
import copy
import random
import uuid
from datetime import date, timedelta

TODAY = date.today()
DISPUTE_WINDOW_DAYS = 60      # stand-in rule: the transaction date counts as the statement date


def _d(days: int) -> str:
    return (TODAY + timedelta(days=days)).isoformat()


class DeskError(Exception):
    pass


CUSTOMERS = {"RR-10293": "Mei Chen", "RR-20877": "Diego Alvarez", "RR-31002": "Asha Nair"}

_START = {
    "cards": {
        "4821": {"customer": "RR-10293", "product": "Cashback Card", "status": "active"},
        "1177": {"customer": "RR-10293", "product": "Everyday Checking debit card", "status": "active"},
        "9034": {"customer": "RR-20877", "product": "Voyager Travel Card", "status": "active"},
        "5560": {"customer": "RR-31002", "product": "Student Checking debit card", "status": "frozen"},
    },
    "transactions": {
        "TX-1001": {"card": "4821", "date": _d(-37), "merchant": "SkyHigh Airlines TKT 0172", "amount_usd": 412.00},
        "TX-1002": {"card": "4821", "date": _d(-37), "merchant": "SkyHigh Airlines TKT 0172", "amount_usd": 412.00},
        "TX-1003": {"card": "4821", "date": _d(-34), "merchant": "Northside Pharmacy", "amount_usd": 18.40},
        "TX-1004": {"card": "4821", "date": _d(-26), "merchant": "StreamBox Subscription", "amount_usd": 12.99},
        "TX-1005": {"card": "4821", "date": _d(-9), "merchant": "GreenLeaf Grocery", "amount_usd": 54.20},
        "TX-1006": {"card": "4821", "date": _d(-75), "merchant": "Harbor Hotel", "amount_usd": 260.00},
        "TX-1101": {"card": "1177", "date": _d(-5), "merchant": "City Metro Transit", "amount_usd": 2.75},
        "TX-2001": {"card": "9034", "date": _d(-6), "merchant": "QuickFix Electronics", "amount_usd": 899.00},
        "TX-2002": {"card": "9034", "date": _d(-12), "merchant": "Tokyo Ramen House", "amount_usd": 31.50},
        "TX-3001": {"card": "5560", "date": _d(-3), "merchant": "Campus Bookshop", "amount_usd": 46.80},
    },
    "disputes": {},           # txn_id -> dispute record
}
STATE = copy.deepcopy(_START)
ACTIONS: list[dict] = []          # every successful write, in order: the audit log
_DONE: dict[str, dict] = {}       # idempotency key -> result already returned
FLAKY = {"rate": 0.0, "rng": random.Random(7)}


def reset(flaky_rate: float = 0.0, seed: int = 7):
    STATE.clear()
    STATE.update(copy.deepcopy(_START))
    ACTIONS.clear()
    _DONE.clear()
    FLAKY.update(rate=flaky_rate, rng=random.Random(seed))


def _maybe_fail(service: str):
    """Chaos for Drill 07.8: real services time out now and then."""
    if FLAKY["rate"] and FLAKY["rng"].random() < FLAKY["rate"]:
        raise TimeoutError(f"{service} timed out; it is safe to retry")


def _own_card(customer: str, card_last4: str) -> dict:
    c = STATE["cards"].get(card_last4.strip()[-4:])
    if c is None or c["customer"] != customer:
        raise DeskError(f"card ending {card_last4} is not one of this customer's cards; "
                        "call the my_cards tool yourself to get their real cards")
    return c


def _own_txn(customer: str, txn_id: str) -> dict:
    t = STATE["transactions"].get(txn_id.strip().upper())
    if t is None or STATE["cards"][t["card"]]["customer"] != customer:
        raise DeskError(f"{txn_id} is not a payment on this customer's cards; "
                        "call recent_transactions to get the real transaction IDs")
    return t


# ---------------------------------------------------------------- reads
def my_cards(customer: str) -> list[dict]:
    _maybe_fail("card service")
    return [{"card_last4": last4, "product": c["product"], "status": c["status"]}
            for last4, c in STATE["cards"].items() if c["customer"] == customer]


def card_status(customer: str, card_last4: str) -> dict:
    _maybe_fail("card service")
    c = _own_card(customer, card_last4)
    return {"card_last4": card_last4[-4:], "product": c["product"], "status": c["status"],
            "note": "frozen cards decline payments; direct debits keep working" if c["status"] == "frozen" else ""}


def recent_transactions(customer: str, card_last4: str, days: int = 90) -> list[dict]:
    _maybe_fail("payments service")
    _own_card(customer, card_last4)
    since = (TODAY - timedelta(days=days)).isoformat()
    rows = [{"txn_id": tid, **t} for tid, t in STATE["transactions"].items()
            if t["card"] == card_last4[-4:] and t["date"] >= since]
    return sorted(rows, key=lambda r: r["date"], reverse=True)


def dispute_quote(customer: str, txn_id: str) -> dict:
    """Policy as code: within 60 days, not already disputed; provisional credit within 10 business days."""
    t = _own_txn(customer, txn_id)
    age = (TODAY - date.fromisoformat(t["date"])).days
    if txn_id.upper() in STATE["disputes"]:
        return {"allowed": False, "reason": "this payment is already being disputed",
                "dispute_id": STATE["disputes"][txn_id.upper()]["dispute_id"]}
    if age > DISPUTE_WINDOW_DAYS:
        return {"allowed": False, "reason": f"the payment is {age} days old; disputes must be raised within "
                                            f"{DISPUTE_WINDOW_DAYS} days, so offer a case for the team to review"}
    return {"allowed": True, "amount_usd": t["amount_usd"], "provisional_credit_by": _d(14),
            "reason": f"{age} days old, inside the {DISPUTE_WINDOW_DAYS}-day window"}


# ---------------------------------------------------------------- writes (change state, logged, idempotent)
def _replay(key: str | None):
    """A write already done with this idempotency key returns its first result, before any checks run:
    after the first dispute, 'already being disputed' is true, but a retry isn't an error."""
    return _DONE[key] | {"note": "already done (same idempotency key)"} if key and key in _DONE else None


def _once(key: str | None, action: str, do):
    """Run a write and remember its result under the idempotency key."""
    result = do()
    ACTIONS.append({"action": action, **result})
    if key:
        _DONE[key] = result
    return result


def freeze_card(customer: str, card_last4: str, key: str | None = None) -> dict:
    if (done := _replay(key)) is not None:
        return done
    _maybe_fail("card service")
    c = _own_card(customer, card_last4)
    if c["status"] == "frozen":
        raise DeskError(f"card ending {card_last4} is already frozen; nothing to do")

    def do():
        c["status"] = "frozen"
        return {"card_last4": card_last4[-4:], "status": "frozen"}
    return _once(key, "freeze_card", do)


def open_dispute(customer: str, txn_id: str, reason: str, key: str | None = None) -> dict:
    if (done := _replay(key)) is not None:
        return done
    _maybe_fail("disputes service")
    t = _own_txn(customer, txn_id)
    quote = dispute_quote(customer, txn_id)
    if not quote["allowed"]:
        raise DeskError(f"a dispute isn't possible: {quote['reason']}")

    def do():
        record = {"dispute_id": "DSP-" + uuid.uuid4().hex[:6].upper(), "txn_id": txn_id.upper(),
                  "amount_usd": t["amount_usd"], "reason": reason, "provisional_credit_by": quote["provisional_credit_by"]}
        STATE["disputes"][txn_id.upper()] = record
        return record
    return _once(key, "open_dispute", do)


def create_case(customer: str, category: str, summary: str) -> dict:
    case = {"case_id": "CS-" + uuid.uuid4().hex[:6].upper(), "customer": customer, "category": category,
            "summary": summary}
    ACTIONS.append({"action": "create_case", **case})
    return {"case_id": case["case_id"], "status": "created"}
