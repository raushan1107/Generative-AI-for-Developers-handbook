"""Drill 06.6: calibrate a relevance floor. Top-k always returns k chunks, even for questions your
documents can't answer. Compare the best score for answerable and off-topic questions, then pick a
floor that keeps the first and drops the second."""
import json

from ingest import DATA
from kb_index import load_or_build

IN_SCOPE = [q["question"] for q in json.loads((DATA / "help_questions.json").read_text(encoding="utf-8"))]
OFF_TOPIC = [
    "What is the capital of France?",
    "Can you recommend a good laptop for programming?",
    "Write me a poem about the sea",
    "How do I reverse a list in Python?",
    "What's the weather like in Toronto tomorrow?",
    "Do you sell gift cards?",
    "Is TrainCrest hiring trainers?",
    "Can I bring my dog to a classroom course?",
]

index = load_or_build()


def best(question):
    return index.search(question, k=1)[0]


inside = sorted(((best(q)["score"], q) for q in IN_SCOPE))
outside = sorted(((best(q)["score"], q) for q in OFF_TOPIC), reverse=True)
print("Lowest in-scope scores:")
for score, q in inside[:4]:
    print(f"  {score:.3f}  {q}")
print("Highest off-topic scores:")
for score, q in outside[:4]:
    print(f"  {score:.3f}  {q}")

print(f"\n{'floor':>6} {'answerable kept':>16} {'off-topic dropped':>18}")
for floor in (0.40, 0.45, 0.50, 0.55, 0.60):
    kept = sum(s >= floor for s, _ in inside)
    dropped = sum(s < floor for s, _ in outside)
    print(f"{floor:>6.2f} {kept:>12}/{len(inside)} {dropped:>14}/{len(outside)}")
