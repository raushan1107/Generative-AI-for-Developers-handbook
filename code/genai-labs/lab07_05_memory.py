"""Drill 07.5: long-term memory as a tool. In session 1 the learner states preferences and the
agent stores them with `remember`; session 2 starts fresh (no chat history), recalls them,
and uses them to pick a date."""
from datetime import date

from pydantic import BaseModel, Field

import desk
from agent import Agent, print_step
from desk_tools import SYSTEM, WRITE_TOOLS, kit
from llm import MODEL, get_client
from memory import STATE_DIR, LearnerMemory

memory = LearnerMemory(STATE_DIR / "memory.json")
memory.forget("L-DIEGO", "")              # every fact contains "": start the drill with an empty memory


class FactArgs(BaseModel):
    fact: str = Field(description="A short, lasting preference or fact the learner asked you to remember")


@kit.register(FactArgs, needs_context=True)
def remember(args, context):
    """Save a lasting preference the learner states (for example preferred class days or contact channel),
    so future sessions know it. Never store payment details, passwords or health information."""
    return memory.remember(context["learner"], args.fact)


client = get_client()
context = {"learner": "L-DIEGO"}

print("SESSION 1")
agent = Agent(client, MODEL, kit, SYSTEM, write_tools=WRITE_TOOLS, on_step=print_step)
# A weekday that matches one later AZ-104 session (dates are relative to today in desk.py).
weekday = date.fromisoformat(desk.upcoming_sessions("C110")[1]).strftime("%A")
print(" ", agent.run(f"Please remember that I can only attend classes that start on a {weekday}, "
                     "and that I prefer email over phone calls.", context).answer)
print("  stored:", memory.recall("L-DIEGO"))

print("\nSESSION 2 (new conversation; memory goes into the system prompt)")
agent = Agent(client, MODEL, kit, SYSTEM + "\n\n" + memory.as_prompt("L-DIEGO"),
              write_tools=WRITE_TOOLS, on_step=print_step)
print(" ", agent.run("Which later AZ-104 date would suit me? Don't book anything yet.", context).answer)
print("  available:", [(d, date.fromisoformat(d).strftime("%A")) for d in desk.upcoming_sessions("C110")])
