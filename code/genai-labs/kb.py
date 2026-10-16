"""Drill 06.9: the Company Knowledge Assistant. Ask questions about RR Finance Bank's documents in the
terminal; answers come only from the documents, with checked citations.
Run:  python kb.py            (as a customer: public help centre only)
      python kb.py --staff    (as support staff: help centre + internal documents)"""
import sys

from citations import render
from kb_index import load_or_build
from rag import answer

staff = "--staff" in sys.argv
audience = ("public", "staff") if staff else ("public",)
index = load_or_build()
print(f"RR Finance Bank knowledge assistant ({'staff' if staff else 'customer'} view, "
      f"{sum(c['audience'] in audience for c in index.chunks)} chunks). Empty line to quit.\n")
while question := input("Question: ").strip():
    result = answer(question, audience=audience, index=index)
    if result["found"]:
        print(render(result["answer"], result["sources"], result["report"]))
        if not result["report"]["ok"]:
            print("(warning: some statements could not be matched to a source)")
    else:
        print(result["answer"])
    print()
