"""Drill 06.9: the whole pipeline (rag.py) on questions that test each behaviour:
a simple answer, an answer from two sections, another language, a question the documents
don't cover, and a staff-only question asked by a learner and then by a staff member."""
from citations import render
from rag import answer

CASES = [
    ("public", "How long until my refund shows up on my card?"),
    ("public", "My lab stopped while I was at lunch and now shows LAB-440. Is my work lost, and how long are labs open?"),
    ("public", "¿Cuánto cuesta cambiar la fecha de mi curso tres días antes?"),
    ("public", "Can I bring my dog to a classroom course?"),
    ("public", "Who can approve a refund exception of $300?"),
    ("staff", "Who can approve a refund exception of $300?"),
]

for audience, question in CASES:
    result = answer(question, audience=("public", "staff") if audience == "staff" else ("public",))
    print(f"[{audience}] {question}")
    if result["found"]:
        report = result["report"]
        print(render(result["answer"], result["sources"], report))
        print(f"checks: {'ok' if report['ok'] else {k: v for k, v in report.items() if v and k not in ('ok', 'cited')}}")
    else:
        print(result["answer"], f"(model calls: {result['llm_calls']})")
    print("-" * 80)
