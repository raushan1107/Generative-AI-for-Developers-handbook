"""Module 07: the agent's tools over desk.py. Read tools look things up; write tools change state.
The signed-in learner comes from `context`, set by the app, never from the model.
WRITE_TOOLS lists the tools that need a human's approval; preview() says, in plain words,
exactly what an approval would do, so the human approves an effect, not a function name."""
import functools
import json
from typing import Literal

from pydantic import BaseModel, Field

import desk
from toolkit import Toolkit

kit = Toolkit()
WRITE_TOOLS = {"extend_lab", "reschedule"}


def actionable(func):
    """Errors are observations: return the system's message so the model can recover
    (pick another date, offer a ticket, retry), instead of a generic "tool failed"."""
    @functools.wraps(func)
    def wrapper(args, context):
        try:
            return func(args, context)
        except desk.DeskError as e:
            return {"error": str(e)}
        except TimeoutError as e:
            return {"error": str(e), "retryable": True}
    return wrapper


class NoArgs(BaseModel):
    pass


class EnrolmentArgs(BaseModel):
    enrolment_id: str = Field(description="Enrolment ID like TC-12345, from my_enrolments")


class CourseArgs(BaseModel):
    course_id: str = Field(description="Course ID like C110, from my_enrolments")


class RescheduleArgs(BaseModel):
    enrolment_id: str = Field(description="Enrolment ID like TC-12345")
    new_start: str = Field(description="New start date, YYYY-MM-DD, one of upcoming_sessions")


class TicketArgs(BaseModel):
    category: Literal["scheduling", "billing", "lab_access", "other"]
    summary: str = Field(description="One or two sentences for the support team")


@kit.register(NoArgs, needs_context=True)
@actionable
def my_enrolments(args, context):
    """List the signed-in learner's enrolments: enrolment_id, course_id, course, start date, status."""
    return desk.my_enrolments(context["learner"])


@kit.register(EnrolmentArgs, needs_context=True)
@actionable
def lab_status(args, context):
    """Lab access for one enrolment: open until which date, days left, and whether the free extension is available."""
    return desk.lab_status(context["learner"], args.enrolment_id)


@kit.register(CourseArgs, needs_context=True)
@actionable
def upcoming_sessions(args, context):
    """Upcoming start dates (YYYY-MM-DD) for a course."""
    return desk.upcoming_sessions(args.course_id)


@kit.register(EnrolmentArgs, needs_context=True)
@actionable
def reschedule_quote(args, context):
    """Whether this enrolment can be moved to another date today, and the fee. Call it before reschedule."""
    return desk.reschedule_quote(context["learner"], args.enrolment_id)


@kit.register(EnrolmentArgs, needs_context=True)
@actionable
def extend_lab(args, context):
    """Use the learner's one free 7-day lab extension. Changes the booking: needs the learner's approval."""
    return desk.extend_lab(context["learner"], args.enrolment_id, key=context.get("idempotency_key"))


@kit.register(RescheduleArgs, needs_context=True)
@actionable
def reschedule(args, context):
    """Move an enrolment to another upcoming date of the same course. Changes the booking and may cost $50:
    needs the learner's approval. Call reschedule_quote first."""
    return desk.reschedule(context["learner"], args.enrolment_id, args.new_start, key=context.get("idempotency_key"))


@kit.register(TicketArgs, needs_context=True)
@actionable
def create_ticket(args, context):
    """Create a ticket for the human support team, for anything you can't do yourself."""
    return desk.create_ticket(context["learner"], args.category, args.summary)


def preview(name: str, arguments: str, context: dict) -> str:
    """What an approval would do, in the learner's terms, computed by code (not described by the model)."""
    a = json.loads(arguments or "{}")
    learner = context["learner"]
    try:
        if name == "extend_lab":
            status = desk.lab_status(learner, a["enrolment_id"])
            return (f"Extend the lab for {a['enrolment_id']} by 7 days, free (one-time): "
                    f"open until {status.get('lab_until')} becomes 7 days later.")
        if name == "reschedule":
            quote = desk.reschedule_quote(learner, a["enrolment_id"])
            fee = f"${quote['fee_usd']}" if quote["fee_usd"] else "free"
            return f"Move {a['enrolment_id']} to start on {a['new_start']} ({fee}: {quote['reason']})."
    except (desk.DeskError, KeyError) as e:
        return f"{name} with {arguments} (can't preview: {e})"
    return f"{name} with {arguments}"


SYSTEM = f"""You are Traincrest Assist, acting for the signed-in TrainCrest learner. Today is {desk.TODAY.isoformat()}.
- Use tools to look things up and to act. Never guess or invent enrolment IDs, dates or fees.
- The learner can't see or call tools. Never ask them to; call the tools yourself.
- Start with my_enrolments whenever you need an enrolment ID or course ID.
- Before reschedule, call reschedule_quote and upcoming_sessions.
- extend_lab and reschedule need the learner's approval; the system asks them. If they decline, don't try again.
- If a tool returns an error, use its message: correct the call, choose another option, or offer create_ticket.
- Finish with a short answer (at most 80 words) stating what was done, with dates and fees."""
