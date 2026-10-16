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

CUSTOMER = "RR-10293"
REQUESTS = [
    "Is my Cashback Card still active?",
    "What have I spent on my Cashback Card recently?",
    "Please freeze my debit card.",
]


class Route(BaseModel):
    category: Literal["card_status", "recent_payments", "freeze_card", "other"]
    card_hint: Optional[str]


client = get_client()


def find_card(hint):
    rows = desk.my_cards(CUSTOMER)
    return next((r for r in rows if hint and hint.lower() in r["product"].lower()), rows[0])


def workflow(request):
    calls = 1
    route = client.chat.completions.parse(model=MODEL, response_format=Route, messages=[
        {"role": "system", "content": "Classify the RR Finance Bank customer request. card_hint: a word from the card "
                                      "name they mention (like 'Cashback' or 'debit'), else null."},
        {"role": "user", "content": request}]).choices[0].message.parsed
    card = find_card(route.card_hint)
    try:                                       # workflows need error handling too: systems say no
        if route.category == "card_status":
            facts = desk.card_status(CUSTOMER, card["card_last4"])
        elif route.category == "recent_payments":
            facts = {"card": card["product"], "payments": desk.recent_transactions(CUSTOMER, card["card_last4"])[:5]}
        elif route.category == "freeze_card":
            facts = desk.freeze_card(CUSTOMER, card["card_last4"])   # a real app asks for approval here (07.7)
        else:
            return route.category, calls, "I'll pass this to the support team."
    except desk.DeskError as err:
        facts = {"card": card["product"], "error": str(err)}
    reply = client.chat.completions.create(model=MODEL, messages=[
        {"role": "system", "content": "Reply to the customer in one or two sentences using only these facts."},
        {"role": "user", "content": f"Request: {request}\nFacts: {json.dumps(facts)}"}]).choices[0].message.content
    return route.category, calls + 1, reply.strip()


agent = Agent(client, MODEL, kit, SYSTEM, write_tools=WRITE_TOOLS, approve=lambda *a: (True, "demo"))
for request in REQUESTS:
    desk.reset()
    category, w_calls, w_reply = workflow(request)
    desk.reset()
    result = agent.run(request, {"customer": CUSTOMER})
    print(f"{request}\n  workflow [{category}, {w_calls} model calls]: {w_reply}")
    print(f"  agent    [{len(result.steps)} tool steps, {result.llm_calls} model calls]: {result.answer}\n")
