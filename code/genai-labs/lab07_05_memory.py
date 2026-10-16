"""Drill 07.5: long-term memory as a tool. In session 1 the customer states preferences and the
agent stores them with `remember`; session 2 starts fresh (no chat history), recalls them,
and uses them when it raises a case."""
from pydantic import BaseModel, Field

from agent import Agent, print_step
from desk_tools import SYSTEM, WRITE_TOOLS, kit
from llm import MODEL, get_client
from memory import STATE_DIR, CustomerMemory

memory = CustomerMemory(STATE_DIR / "memory.json")
memory.forget("RR-20877", "")             # every fact contains "": start the drill with an empty memory


class FactArgs(BaseModel):
    fact: str = Field(description="A short, lasting preference or fact the customer asked you to remember")


@kit.register(FactArgs, needs_context=True)
def remember(args, context):
    """Save a lasting preference the customer states (for example how they want to be contacted or when
    they travel), so future sessions know it. Never store card numbers, passwords, PINs or health information."""
    return memory.remember(context["customer"], args.fact)


client = get_client()
context = {"customer": "RR-20877"}

print("SESSION 1")
agent = Agent(client, MODEL, kit, SYSTEM, write_tools=WRITE_TOOLS, on_step=print_step)
print(" ", agent.run("Please remember that I want to be contacted by email only, never by phone, "
                     "and that I'm abroad in Japan every March.", context).answer)
print("  stored:", memory.recall("RR-20877"))

print("\nSESSION 2 (new conversation; memory goes into the system prompt)")
agent = Agent(client, MODEL, kit, SYSTEM + "\n\n" + memory.as_prompt("RR-20877"),
              write_tools=WRITE_TOOLS, on_step=print_step)
print(" ", agent.run("My March statement never arrived. Please raise a case and tell me how the team will "
                     "contact me.", context).answer)
