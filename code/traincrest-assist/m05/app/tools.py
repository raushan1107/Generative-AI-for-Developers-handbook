"""Traincrest Assist tools (milestone 4; search_courses upgraded to semantic search in milestone 5).
The model can ask for these; our code decides whether and how they run.
Identity rule: the signed-in learner comes from `context`, set by the app, never from the model."""
import json
import re
import time
import uuid
from datetime import date
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app import backend, policy
from app.config import TICKETS_FILE
from app.toolkit import Toolkit

kit = Toolkit()
ENROLMENT_ID = re.compile(r"TC-\d{5}")

# Friendly status lines the UI shows while a tool runs.
LABELS = {
    "search_courses": "Searching the course catalogue",
    "get_course": "Looking up the course",
    "list_my_enrolments": "Checking your enrolments",
    "get_voucher_status": "Checking your exam voucher",
    "quote_refund": "Working out your refund under the policy",
    "quote_reschedule": "Checking the reschedule fee",
    "create_support_ticket": "Creating a support ticket",
}


def _signed_in(context: dict) -> str:
    learner_id = context.get("learner_id")
    if learner_id not in backend.LEARNERS:
        raise PermissionError("no learner is signed in; ask them to sign in first")
    return learner_id


def _own_enrolment(enrolment_id: str, context: dict) -> dict:
    learner_id = _signed_in(context)
    record = backend.ENROLMENTS.get(enrolment_id)
    if record is None or record["learner_id"] != learner_id:       # same answer for both: don't leak which IDs exist
        raise PermissionError(f"{enrolment_id} is not one of the signed-in learner's enrolments")
    return record


class EnrolmentArg(BaseModel):
    enrolment_id: str = Field(description="The learner's enrolment ID, like TC-12345")

    @field_validator("enrolment_id")
    @classmethod
    def looks_like_an_id(cls, v):
        v = v.strip().upper()
        if not ENROLMENT_ID.fullmatch(v):
            raise ValueError("must look like TC-12345")
        return v


# ---------------------------------------------------------------- catalogue (no identity needed)
_search = None          # the SearchService, set by the app at start-up (milestone 5)


def set_search_service(service):
    global _search
    _search = service


class SearchCoursesArgs(BaseModel):
    query: str = Field(description="What the learner is looking for, in their own words, e.g. 'make apps that understand photos'")
    level: Optional[Literal["beginner", "intermediate", "advanced"]] = None
    max_price_usd: Optional[int] = Field(default=None, description="Highest price in USD, or null")
    format: Optional[Literal["live-online", "classroom", "self-paced"]] = None


@kit.register(SearchCoursesArgs)
def search_courses(args):
    """Find TrainCrest courses that match what the learner describes (semantic + keyword search),
    optionally filtered by level, maximum price and format."""
    filters = {"kind": "course", "level": args.level, "max_price_usd": args.max_price_usd, "format": args.format}
    if _search is not None:
        try:
            hits = _search.search(args.query, k=5, **filters)
            return [{k: h[k] for k in ("id", "title", "level", "format", "price_usd")} for h in hits]
        except Exception:                     # embedding service down: degrade instead of failing
            pass
    # No index yet, or search failed: fall back to milestone 4's keyword filter so the assistant still works.
    words = [w for w in args.query.lower().split() if len(w) > 3]
    hits = [c for c in backend.COURSES.values()
            if (not args.level or c["level"] == args.level)
            and (args.max_price_usd is None or c["price_usd"] <= args.max_price_usd)
            and (not args.format or c["format"] == args.format)
            and (not words or any(w in (c["title"] + " " + c["description"]).lower() for w in words))]
    return [{k: c[k] for k in ("id", "title", "level", "format", "price_usd")} for c in hits[:5]]


class CourseArgs(BaseModel):
    course_id: str = Field(description="Course ID like C104")


@kit.register(CourseArgs)
def get_course(args):
    """Full details of one course: description, level, format, duration and price."""
    return backend.COURSES.get(args.course_id.strip().upper()) or {"error": f"no course {args.course_id}"}


# ---------------------------------------------------------------- the signed-in learner's data
class NoArgs(BaseModel):
    pass


@kit.register(NoArgs, needs_context=True)
def list_my_enrolments(args, context):
    """List the signed-in learner's enrolments with course, start date, status and attendance."""
    rows = backend.enrolments_of(_signed_in(context))
    return [{k: r[k] for k in ("enrolment_id", "course_title", "start_date", "status", "attendance_pct")} for r in rows]


@kit.register(EnrolmentArg, needs_context=True)
def get_voucher_status(args, context):
    """Exam voucher status for one of the signed-in learner's enrolments."""
    _own_enrolment(args.enrolment_id, context)
    return backend.VOUCHERS.get(args.enrolment_id, {"status": "none", "note": "this course has no exam voucher"})


@kit.register(EnrolmentArg, needs_context=True)
def quote_refund(args, context):
    """Refund the learner would get if they cancelled this enrolment today, under TrainCrest policy.
    Always use this for refund amounts; never calculate them yourself."""
    e = _own_enrolment(args.enrolment_id, context)
    quote = policy.refund_quote(date.fromisoformat(e["start_date"]), date.today(), e["paid_usd"])
    return {"enrolment_id": args.enrolment_id, "paid_usd": e["paid_usd"], **quote}


@kit.register(EnrolmentArg, needs_context=True)
def quote_reschedule(args, context):
    """Whether this enrolment can move to a later date today, and the fee."""
    e = _own_enrolment(args.enrolment_id, context)
    return {"enrolment_id": args.enrolment_id, **policy.reschedule_fee(date.fromisoformat(e["start_date"]), date.today())}


class TicketArgs(BaseModel):
    category: Literal["scheduling", "billing", "exam_voucher", "certificate", "lab_access", "account", "other"]
    summary: str = Field(description="One or two sentences for the support team, in English")
    enrolment_id: Optional[str] = Field(default=None, description="Related enrolment ID, or null")
    urgency: Literal["low", "medium", "high"]

    @field_validator("summary")
    @classmethod
    def summary_length(cls, v):
        v = v.strip()
        if not 10 <= len(v) <= 400:
            raise ValueError("summary must be 10 to 400 characters")
        return v

    @field_validator("enrolment_id")
    @classmethod
    def id_format(cls, v):
        if v is not None and not ENROLMENT_ID.fullmatch(v.strip().upper()):
            raise ValueError("enrolment_id must look like TC-12345")
        return v.strip().upper() if v else v


@kit.register(TicketArgs, needs_context=True)
def create_support_ticket(args, context):
    """Create a ticket for the human support team. Use it for refunds or cancellations, exceptions,
    anything you can't resolve, or when the learner asks for a person. Tell the learner the ticket ID."""
    learner_id = _signed_in(context)
    if args.enrolment_id:
        _own_enrolment(args.enrolment_id, context)
    ticket = {"ticket_id": "T-" + uuid.uuid4().hex[:6].upper(), "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
              "learner_id": learner_id, **args.model_dump()}
    path = Path(TICKETS_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:        # Module 07 adds human approval before actions like this
        f.write(json.dumps(ticket, ensure_ascii=False) + "\n")
    return {"ticket_id": ticket["ticket_id"], "status": "created", "team": args.category}


TOOLS = kit.schemas()
