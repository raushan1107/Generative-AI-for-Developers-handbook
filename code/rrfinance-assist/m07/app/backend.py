"""Stand-in for TrainCrest's real systems (catalogue, enrolments, vouchers). Fictional data.
In a real company these are existing APIs or databases; the assistant only calls them through tools.
Dates are relative to today so the demo always has upcoming and finished courses."""
import json
from datetime import date, timedelta
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
COURSES = {c["id"]: c for c in json.loads((DATA / "courses.json").read_text(encoding="utf-8"))}


def _day(offset: int) -> str:
    return (date.today() + timedelta(days=offset)).isoformat()


LEARNERS = {
    "L-MEI": {"name": "Mei Chen", "email": "mei@example.com"},
    "L-DIEGO": {"name": "Diego Alvarez", "email": "diego@example.com"},
    "L-ASHA": {"name": "Asha Nair", "email": "asha@example.com"},
}

ENROLMENTS = {
    "TC-10293": {"learner_id": "L-MEI", "course_id": "C112", "start_date": _day(-16), "status": "completed",
                 "attendance_pct": 92, "paid_usd": 1350, "retake_pass": False},
    "TC-10477": {"learner_id": "L-MEI", "course_id": "C106", "start_date": _day(10), "status": "confirmed",
                 "attendance_pct": None, "paid_usd": 1290, "retake_pass": False},
    "TC-20877": {"learner_id": "L-DIEGO", "course_id": "C110", "start_date": _day(5), "status": "confirmed",
                 "attendance_pct": None, "paid_usd": 1250, "retake_pass": True},
    "TC-31002": {"learner_id": "L-ASHA", "course_id": "C109", "start_date": _day(-3), "status": "completed",
                 "attendance_pct": 100, "paid_usd": 350, "retake_pass": False},
    "TC-31188": {"learner_id": "L-ASHA", "course_id": "C104", "start_date": _day(21), "status": "confirmed",
                 "attendance_pct": None, "paid_usd": 1490, "retake_pass": False},
}

VOUCHERS = {
    "TC-10293": {"exam": "AI-102", "status": "issued", "issued_on": _day(-9), "expires_on": _day(-9 + 365),
                 "code_hint": "ends in 7Q4K"},
    "TC-31002": {"exam": "AZ-900", "status": "pending", "due_by": _day(2)},
    "TC-20877": {"exam": "AZ-104", "status": "not_yet_eligible", "note": "issued after the course is completed"},
}


def enrolments_of(learner_id: str) -> list[dict]:
    return [{"enrolment_id": eid, **e, "course_title": COURSES[e["course_id"]]["title"]}
            for eid, e in ENROLMENTS.items() if e["learner_id"] == learner_id]


# ---------------------------------------------------------------- milestone 7: things that can change
# Lab access per enrolment, and the dates each course runs. Writes go through the two functions
# below, which re-check the rules, are idempotent (same key, same result, done once) and are logged.
LABS = {
    "TC-10293": {"lab_until": _day(4), "free_extension_used": False},
    "TC-31002": {"lab_until": _day(27), "free_extension_used": True},
}
SESSIONS = {"C104": [_day(21), _day(35)], "C106": [_day(10), _day(24), _day(38)],
            "C109": [_day(8), _day(22)], "C110": [_day(5), _day(17), _day(33)], "C112": [_day(12), _day(40)]}
ACTIONS_FILE = DATA / "actions.jsonl"
_DONE: dict[str, dict] = {}


class ActionError(Exception):
    """A rule says no. The message is safe to show to the learner."""


def upcoming_sessions(course_id: str) -> list[str]:
    return [d for d in SESSIONS.get(course_id, []) if d > date.today().isoformat()]


def _log(action: str, record: dict):
    ACTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with ACTIONS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"action": action, "at": date.today().isoformat(), **record}) + "\n")


def extend_lab(enrolment_id: str, key: str) -> dict:
    if key in _DONE:                                     # a retry of an action already done: same answer
        return _DONE[key]
    lab = LABS.get(enrolment_id)
    if lab is None:
        raise ActionError("This enrolment has no lab access to extend.")
    if lab["free_extension_used"]:
        raise ActionError("The free 7-day extension has already been used.")
    lab["lab_until"] = (date.fromisoformat(lab["lab_until"]) + timedelta(days=7)).isoformat()
    lab["free_extension_used"] = True
    _DONE[key] = result = {"enrolment_id": enrolment_id, "lab_until": lab["lab_until"], "fee_usd": 0}
    _log("extend_lab", {"key": key, **result})
    return result


def reschedule(enrolment_id: str, new_start: str, fee_usd: int, key: str) -> dict:
    if key in _DONE:
        return _DONE[key]
    e = ENROLMENTS[enrolment_id]
    if new_start not in upcoming_sessions(e["course_id"]) or new_start == e["start_date"]:
        raise ActionError(f"{new_start} is no longer an available date for this course.")
    old, e["start_date"] = e["start_date"], new_start
    _DONE[key] = result = {"enrolment_id": enrolment_id, "old_start": old, "new_start": new_start, "fee_usd": fee_usd}
    _log("reschedule", {"key": key, **result})
    return result
