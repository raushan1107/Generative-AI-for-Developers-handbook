"""Drill 07.7: human in the loop. Write tools pause the agent and show the customer exactly what
will happen (computed by code), and nothing changes unless they say yes.
Run:  python lab07_07_approval.py          (you answer y/n)
      python lab07_07_approval.py --no     (decline automatically, for a scripted demo)"""
import sys

import desk
from agent import Agent, print_step
from desk_tools import SYSTEM, WRITE_TOOLS, kit, preview
from llm import MODEL, get_client


def ask_customer(name, arguments, context):
    print(f"\n  APPROVAL NEEDED: {preview(name, arguments, context)}")
    if "--no" in sys.argv or "--yes" in sys.argv:
        answer = "y" if "--yes" in sys.argv else "n"
        print(f"  Approve? [y/n] {answer}")
    else:
        answer = input("  Approve? [y/n] ").strip().lower()
    return (answer == "y", "approved" if answer == "y" else "the customer said no")


before = desk.card_status("RR-10293", "4821")["status"]
agent = Agent(get_client(), MODEL, kit, SYSTEM, write_tools=WRITE_TOOLS, approve=ask_customer, on_step=print_step)
result = agent.run("Please freeze my Cashback Card.", {"customer": "RR-10293"})
print(f"\nANSWER: {result.answer}")
print(f"card ending 4821: {before} -> {desk.card_status('RR-10293', '4821')['status']}")
print("audit log:", desk.ACTIONS or "no changes")
