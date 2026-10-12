"""Drill 07.4: a workflow vs an agent for the same requests.
Workflow: one model call routes the request into a fixed category (structured output); code runs
the steps for that category; one more call writes the reply from the facts. Predictable and cheap.
Agent: the model chooses every step. Flexible, but more calls and less predictable."""
import json
from typing import Literal, Optional

from pydantic import BaseModel

import desk
from agent import Agent
from desk_tools import SYSTEM, WRITE_TOOLS, kit
from llm import MODEL, get_client

LEARNER = "L-MEI"
REQUESTS = [
    "How long is my AI-102 lab still open?",
    "When are the next dates for my RAG course?",
    "Please extend my AI-102 lab.",
]


class Route(BaseModel):
    category: Literal["lab_status", "next_dates", "extend_lab", "other"]
    course_hint: Optional[str]


client = get_client()


def find_enrolment(hint):
    rows = desk.my_enrolments(LEARNER)
    return next((r for r in rows if hint and hint.lower() in r["course"].lower()), rows[0])


def workflow(request):
    calls = 1
    route = client.chat.completions.parse(model=MODEL, response_format=Route, messages=[
        {"role": "system", "content": "Classify the TrainCrest learner request. course_hint: a word from the course "
                                      "name they mention (like 'AI-102' or 'RAG'), else null."},
        {"role": "user", "content": request}]).choices[0].message.parsed
    e = find_enrolment(route.course_hint)
    try:                                       # workflows need error handling too: systems say no
        if route.category == "lab_status":
            facts = desk.lab_status(LEARNER, e["enrolment_id"])
        elif route.category == "next_dates":
            facts = {"course": e["course"], "dates": desk.upcoming_sessions(e["course_id"])}
        elif route.category == "extend_lab":
            facts = desk.extend_lab(LEARNER, e["enrolment_id"])    # a real app asks for approval here (07.7)
        else:
            return route.category, calls, "I'll pass this to the support team."
    except desk.DeskError as err:
        facts = {"course": e["course"], "error": str(err)}
    reply = client.chat.completions.create(model=MODEL, messages=[
        {"role": "system", "content": "Reply to the learner in one or two sentences using only these facts."},
        {"role": "user", "content": f"Request: {request}\nFacts: {json.dumps(facts)}"}]).choices[0].message.content
    return route.category, calls + 1, reply.strip()


agent = Agent(client, MODEL, kit, SYSTEM, write_tools=WRITE_TOOLS, approve=lambda *a: (True, "demo"))
for request in REQUESTS:
    desk.reset()
    category, w_calls, w_reply = workflow(request)
    desk.reset()
    result = agent.run(request, {"learner": LEARNER})
    print(f"{request}\n  workflow [{category}, {w_calls} model calls]: {w_reply}")
    print(f"  agent    [{len(result.steps)} tool steps, {result.llm_calls} model calls]: {result.answer}\n")
