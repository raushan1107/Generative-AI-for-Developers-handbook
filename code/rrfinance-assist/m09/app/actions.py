"""Actions that need the customer's approval (milestone 7).

The model can only PROPOSE a change (request_card_freeze, request_dispute in tools.py).
A proposal is stored here with frozen arguments and a summary written by code. Nothing happens
until the customer presses Approve. Then code re-checks the rules and executes it once
(the action id is the idempotency key). The model never approves its own actions."""
import time
import uuid
from datetime import date

from app import backend, policy

EXPIRY_S = 15 * 60                     # a proposal older than this must be asked for again


def new_action_id() -> str:
    return "A-" + uuid.uuid4().hex[:6].upper()


class ActionStore:
    def __init__(self):
        self.pending: dict[str, dict] = {}         # action_id -> proposal (in memory; Module 08 persists it)

    def add(self, session_id: str, proposal: dict):
        self.pending[proposal["action_id"]] = {**proposal, "session_id": session_id, "created": time.time()}

    def for_session(self, session_id: str) -> list[dict]:
        return [p for p in self.pending.values() if p["session_id"] == session_id]

    def decide(self, session_id: str, action_id: str, customer_id: str | None, approve: bool) -> dict:
        """Returns {"status": done|declined|expired|failed|unknown, "message": text for the customer}."""
        p = self.pending.get(action_id)
        if p is None or p["session_id"] != session_id or p["customer_id"] != customer_id:
            return {"status": "unknown", "message": "That request isn't waiting for approval any more."}
        del self.pending[action_id]                # one decision per proposal, whatever happens next
        if not approve:
            return {"status": "declined", "message": f"OK, I haven't changed anything ({p['summary']})."}
        if time.time() - p["created"] > EXPIRY_S:
            return {"status": "expired", "message": "That request has expired. Please ask me again."}
        try:
            return {"status": "done", "message": EXECUTE[p["tool"]](p, action_id)}
        except backend.ActionError as e:
            return {"status": "failed", "message": f"I couldn't do that: {e}"}


def _freeze(p, key):
    r = backend.freeze_card(p["args"]["card_last4"], key=key)
    return (f"Done: your card ending {r['card_last4']} is frozen. New payments and cash withdrawals will be "
            "declined until you unfreeze it in the app; direct debits keep working.")


def _dispute(p, key):
    t = backend.TRANSACTIONS[p["args"]["txn_id"]]
    quote = policy.dispute_quote(date.fromisoformat(t["date"]), date.today())     # re-check: time has passed
    if not quote["allowed"]:
        raise backend.ActionError("the 60-day dispute window has closed since you were asked; please ask me again")
    r = backend.open_dispute(p["args"]["txn_id"], p["args"]["reason"], quote["provisional_credit_by"], key=key)
    return (f"Done: dispute {r['dispute_id']} is open for ${r['amount_usd']:.2f}. You'll get a provisional credit "
            f"by {r['provisional_credit_by']} while we investigate.")


EXECUTE = {"request_card_freeze": _freeze, "request_dispute": _dispute}
