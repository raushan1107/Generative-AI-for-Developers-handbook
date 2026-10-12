"""Module 07: stand-in TrainCrest systems for the agent drills (fictional, in memory).
Read functions look things up; write functions change state and are recorded in ACTIONS.
Dates are relative to today, so there are always upcoming and finished courses.
Errors are DeskError with a message an agent can act on ("use upcoming_sessions to see dates")."""
import copy
import random
import uuid
from datetime import date, timedelta

TODAY = date.today()


def _d(days: int) -> str:
    return (TODAY + timedelta(days=days)).isoformat()


class DeskError(Exception):
    pass


LEARNERS = {"L-MEI": "Mei Chen", "L-DIEGO": "Diego Alvarez", "L-ASHA": "Asha Nair"}

_START = {
    "enrolments": {
        "TC-10293": {"learner": "L-MEI", "course_id": "C112", "course": "AI-102: Azure AI Engineer",
                     "start": _d(-16), "status": "completed", "lab_until": _d(4), "free_extension_used": False},
        "TC-10477": {"learner": "L-MEI", "course_id": "C106", "course": "Building RAG Applications",
                     "start": _d(10), "status": "confirmed", "lab_until": None, "free_extension_used": False},
        "TC-20877": {"learner": "L-DIEGO", "course_id": "C110", "course": "AZ-104: Azure Administrator",
                     "start": _d(5), "status": "confirmed", "lab_until": None, "free_extension_used": False,
                     "late_reschedule_used": False},
        "TC-31002": {"learner": "L-ASHA", "course_id": "C109", "course": "AZ-900: Azure Fundamentals",
                     "start": _d(-3), "status": "completed", "lab_until": _d(28), "free_extension_used": True},
    },
    "sessions": {"C106": [_d(10), _d(24), _d(38)], "C110": [_d(5), _d(17), _d(33)],
                 "C112": [_d(12), _d(40)], "C109": [_d(8), _d(22)]},
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


def _own(learner: str, enrolment_id: str) -> dict:
    e = STATE["enrolments"].get(enrolment_id.strip().upper())
    if e is None or e["learner"] != learner:
        raise DeskError(f"{enrolment_id} is not one of this learner's enrolments; "
                        "call the my_enrolments tool yourself to get their real enrolment IDs")
    return e


# ---------------------------------------------------------------- reads
def my_enrolments(learner: str) -> list[dict]:
    _maybe_fail("enrolment service")
    return [{"enrolment_id": eid, "course_id": e["course_id"], "course": e["course"], "start": e["start"],
             "status": e["status"]} for eid, e in STATE["enrolments"].items() if e["learner"] == learner]


def lab_status(learner: str, enrolment_id: str) -> dict:
    _maybe_fail("lab service")
    e = _own(learner, enrolment_id)
    if not e["lab_until"]:
        return {"enrolment_id": enrolment_id, "lab": "not started", "note": "labs open when the course starts"}
    days_left = (date.fromisoformat(e["lab_until"]) - TODAY).days
    return {"enrolment_id": enrolment_id, "lab_until": e["lab_until"], "days_left": days_left,
            "free_extension_available": not e["free_extension_used"]}


def upcoming_sessions(course_id: str) -> list[str]:
    _maybe_fail("schedule service")
    return [d for d in STATE["sessions"].get(course_id.strip().upper(), []) if d > TODAY.isoformat()]


def reschedule_quote(learner: str, enrolment_id: str) -> dict:
    """Policy as code: free 7+ days before the start; within 7 days, once for $50; not after the start."""
    e = _own(learner, enrolment_id)
    days = (date.fromisoformat(e["start"]) - TODAY).days
    if days < 0:
        return {"allowed": False, "fee_usd": None, "reason": "the course has already started"}
    if days >= 7:
        return {"allowed": True, "fee_usd": 0, "reason": "7 or more days before the start"}
    if e.get("late_reschedule_used"):
        return {"allowed": False, "fee_usd": None, "reason": "the one late reschedule was already used"}
    return {"allowed": True, "fee_usd": 50, "reason": "within 7 days of the start: one reschedule for $50"}


# ---------------------------------------------------------------- writes (change state, logged, idempotent)
def _replay(key: str | None):
    """A write already done with this idempotency key returns its first result, before any checks run:
    after the first extension, 'free extension already used' is true, but a retry isn't an error."""
    return _DONE[key] | {"note": "already done (same idempotency key)"} if key and key in _DONE else None


def _once(key: str | None, action: str, do):
    """Run a write and remember its result under the idempotency key."""
    result = do()
    ACTIONS.append({"action": action, **result})
    if key:
        _DONE[key] = result
    return result


def extend_lab(learner: str, enrolment_id: str, key: str | None = None) -> dict:
    if (done := _replay(key)) is not None:
        return done
    _maybe_fail("lab service")
    e = _own(learner, enrolment_id)
    if not e["lab_until"]:
        raise DeskError("the lab hasn't started yet, so it can't be extended")
    if e["free_extension_used"]:
        raise DeskError("the free 7-day extension was already used; 14 more days cost $49 and are bought "
                        "in My Learning, so offer to raise a ticket instead")

    def do():
        e["lab_until"] = (date.fromisoformat(e["lab_until"]) + timedelta(days=7)).isoformat()
        e["free_extension_used"] = True
        return {"enrolment_id": enrolment_id, "lab_until": e["lab_until"], "fee_usd": 0}
    return _once(key, "extend_lab", do)


def reschedule(learner: str, enrolment_id: str, new_start: str, key: str | None = None) -> dict:
    if (done := _replay(key)) is not None:
        return done
    _maybe_fail("schedule service")
    e = _own(learner, enrolment_id)
    quote = reschedule_quote(learner, enrolment_id)
    if not quote["allowed"]:
        raise DeskError(f"rescheduling isn't possible: {quote['reason']}")
    if new_start not in upcoming_sessions(e["course_id"]) or new_start == e["start"]:
        raise DeskError(f"{new_start} is not an available date; use upcoming_sessions('{e['course_id']}')")

    def do():
        old = e["start"]
        e["start"] = new_start
        if quote["fee_usd"]:
            e["late_reschedule_used"] = True
        return {"enrolment_id": enrolment_id, "old_start": old, "new_start": new_start, "fee_usd": quote["fee_usd"]}
    return _once(key, "reschedule", do)


def create_ticket(learner: str, category: str, summary: str) -> dict:
    ticket = {"ticket_id": "T-" + uuid.uuid4().hex[:6].upper(), "learner": learner, "category": category,
              "summary": summary}
    ACTIONS.append({"action": "create_ticket", **ticket})
    return {"ticket_id": ticket["ticket_id"], "status": "created"}
