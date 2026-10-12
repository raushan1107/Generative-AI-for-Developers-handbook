"""Drill 07.7: human in the loop. Write tools pause the agent and show the learner exactly what
will happen (computed by code), and nothing changes unless they say yes.
Run:  python lab07_07_approval.py          (you answer y/n)
      python lab07_07_approval.py --no     (decline automatically, for a scripted demo)"""
import sys

import desk
from agent import Agent, print_step
from desk_tools import SYSTEM, WRITE_TOOLS, kit, preview
from llm import MODEL, get_client


def ask_learner(name, arguments, context):
    print(f"\n  APPROVAL NEEDED: {preview(name, arguments, context)}")
    if "--no" in sys.argv or "--yes" in sys.argv:
        answer = "y" if "--yes" in sys.argv else "n"
        print(f"  Approve? [y/n] {answer}")
    else:
        answer = input("  Approve? [y/n] ").strip().lower()
    return (answer == "y", "approved" if answer == "y" else "the learner said no")


before = desk.lab_status("L-MEI", "TC-10293")["lab_until"]
agent = Agent(get_client(), MODEL, kit, SYSTEM, write_tools=WRITE_TOOLS, approve=ask_learner, on_step=print_step)
result = agent.run("Please extend my AI-102 lab.", {"learner": "L-MEI"})
print(f"\nANSWER: {result.answer}")
print(f"lab open until: {before} -> {desk.lab_status('L-MEI', 'TC-10293')['lab_until']}")
print("audit log:", desk.ACTIONS or "no changes")
