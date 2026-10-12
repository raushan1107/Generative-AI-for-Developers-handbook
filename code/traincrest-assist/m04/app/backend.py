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
