"""Actions that need the learner's approval (milestone 7).

The model can only PROPOSE a change (request_lab_extension, request_reschedule in tools.py).
A proposal is stored here with frozen arguments and a summary written by code. Nothing happens
until the learner presses Approve. Then code re-checks the rules and executes it once
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

    def decide(self, session_id: str, action_id: str, learner_id: str | None, approve: bool) -> dict:
        """Returns {"status": done|declined|expired|failed|unknown, "message": text for the learner}."""
        p = self.pending.get(action_id)
        if p is None or p["session_id"] != session_id or p["learner_id"] != learner_id:
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


def _extend(p, key):
    r = backend.extend_lab(p["args"]["enrolment_id"], key=key)
    return f"Done: your lab for {r['enrolment_id']} is now open until {r['lab_until']} (free)."


def _reschedule(p, key):
    e = backend.ENROLMENTS[p["args"]["enrolment_id"]]
    fee = policy.reschedule_fee(date.fromisoformat(e["start_date"]), date.today())   # re-check: time has passed
    if not fee["allowed"] or fee["fee_usd"] != p["fee_usd"]:
        raise backend.ActionError("the fee or rules changed since you were asked; please ask me again")
    r = backend.reschedule(p["args"]["enrolment_id"], p["args"]["new_start"], fee["fee_usd"], key=key)
    cost = f"${r['fee_usd']} fee" if r["fee_usd"] else "no fee"
    return f"Done: {r['enrolment_id']} now starts on {r['new_start']} (was {r['old_start']}; {cost})."


EXECUTE = {"request_lab_extension": _extend, "request_reschedule": _reschedule}
