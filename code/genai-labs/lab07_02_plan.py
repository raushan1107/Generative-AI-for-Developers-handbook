"""Drill 07.2: plan first, as structured output, then let code check the plan before anything runs.
Run:  python lab07_02_plan.py "I'm Mei. I was charged twice for my SkyHigh flight..." """
import sys

from pydantic import BaseModel, Field

from desk_tools import WRITE_TOOLS, kit
from llm import MODEL, get_client

REQUEST = sys.argv[1] if len(sys.argv) > 1 else (
    "I'm Mei. I was charged twice for my SkyHigh Airlines ticket on my Cashback Card. Dispute the "
    "duplicate if it's still possible, tell me when I'd get the money back, and check the card is active.")


class PlanStep(BaseModel):
    tool: str = Field(description="One of the available tool names")
    purpose: str = Field(description="Why this step is needed, in a few words")
    needs_approval: bool = Field(description="True if this step changes something for the customer")


class Plan(BaseModel):
    goal: str
    steps: list[PlanStep]
    ask_customer_first: list[str] = Field(description="Questions to ask before acting, if anything is unclear")


tools = "\n".join(f"- {t['function']['name']}: {t['function']['description']}" for t in kit.schemas())
prompt = f"""Plan how to handle this RR Finance Bank customer request with the tools below. Don't execute anything.
Order the steps so each one has the information it needs. Mark steps that change something.

Tools:
{tools}

Request: {REQUEST}"""

plan = get_client().chat.completions.parse(model=MODEL, messages=[{"role": "user", "content": prompt}],
                                            response_format=Plan).choices[0].message.parsed
print("GOAL:", plan.goal)
for n, step in enumerate(plan.steps, 1):
    print(f"  {n}. {step.tool:20} {'[needs approval] ' if step.needs_approval else ''}{step.purpose}")
for q in plan.ask_customer_first:
    print("  ask first:", q)

# Code checks the plan: the model proposes, the program disposes.
names = [s.tool for s in plan.steps]
problems = [f"unknown tool: {n}" for n in names if n not in kit.tools]
problems += [f"{s.tool} changes data but isn't marked for approval" for s in plan.steps
             if s.tool in WRITE_TOOLS and not s.needs_approval]
if "open_dispute" in names:
    before = names[:names.index("open_dispute")]
    problems += [f"open_dispute planned before {t}" for t in ("recent_transactions", "dispute_quote") if t not in before]
# Dependencies: these tools need a card or a transaction ID, which only my_cards (and then
# recent_transactions) provide.
needs_ids = [i for i, n in enumerate(names) if n not in ("my_cards", "create_case")]
if needs_ids and "my_cards" not in names[:needs_ids[0]]:
    problems.append(f"{names[needs_ids[0]]} needs a card, but my_cards isn't called before it")
problems += [f"{n} (a write) is planned more than once" for n in sorted(WRITE_TOOLS) if names.count(n) > 1]
print("\nPLAN CHECK:", "OK" if not problems else problems)
