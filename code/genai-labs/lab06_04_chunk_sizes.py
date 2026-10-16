"""Drill 06.4: chunking for answers. Retrieval must find the answer (hit@3), but everything
retrieved is also sent to the model, so context size is cost and noise. Measure both."""
import json
import re

from ingest import DATA, load_folder
from kb_index import KnowledgeIndex
from rag_chunks import chunk_all
from rag_prompt import count_tokens

QUESTIONS = json.loads((DATA / "help_questions.json").read_text(encoding="utf-8"))
# Five more whose answers sit in an article's introduction, before its first '## ' heading.
INTRO_QUESTIONS = [
    {"question": "I don't recognise a payment, should I dispute it?", "source": "card-disputes",
     "must_contain": "that is fraud, not a dispute"},
    {"question": "How long does it take to open an account in the app?", "source": "account-opening",
     "must_contain": "about 10 minutes"},
    {"question": "What decides the interest rate on my loan?", "source": "loans-and-mortgages",
     "must_contain": "depends on your credit history"},
    {"question": "Is the fraud team open at night?", "source": "fraud-and-scams",
     "must_contain": "24 hours a day, 7 days a week"},
    {"question": "Where can I see the full list of fees?", "source": "fees-and-charges",
     "must_contain": "Your account terms list every fee"},
]
docs, _ = load_folder(DATA / "help", "public")


def milestone5_chunks(docs):
    """Milestone 5's chunker: one chunk per '## ' section, text before the first heading dropped."""
    out = []
    for d in docs:
        for n, part in enumerate(re.split(r"^## ", d.text, flags=re.M)[1:], 1):
            heading, _, body = part.partition("\n")
            out.append({"id": f"{d.id}#{n}", "doc_id": d.id, "title": f"{d.title} > {heading}", "source": d.source,
                        "text": f"{d.title} > {heading}\n{body.strip()}", "audience": "public"})
    return out


def whole_documents(docs):
    return [{"id": d.id, "doc_id": d.id, "title": d.title, "text": d.text, "source": d.source, "audience": "public"}
            for d in docs]


STRATEGIES = {
    "whole articles": whole_documents(docs),
    "M5 sections (no intros)": milestone5_chunks(docs),
    "sections + intros, max 900": chunk_all(docs, max_chars=900),
    "sections + intros, max 200": chunk_all(docs, max_chars=200),
}
print(f"{'strategy':28} {'chunks':>6} {'hit@3 (20)':>11} {'intro (5)':>10} {'tokens sent':>12}")
for name, chunks in STRATEGIES.items():
    index, _ = KnowledgeIndex.build(chunks)
    scores, tokens = [], 0
    for questions in (QUESTIONS, INTRO_QUESTIONS):
        hits = 0
        for q in questions:
            top = index.search(q["question"], k=3)
            tokens += sum(count_tokens(h["text"]) for h in top)
            hits += any(h["doc_id"] == q["source"] and q["must_contain"] in h["text"] for h in top)
        scores.append(hits)
    asked = len(QUESTIONS) + len(INTRO_QUESTIONS)
    print(f"{name:28} {len(chunks):>6} {scores[0]:>8}/20 {scores[1]:>8}/5 {tokens / asked:>8.0f} avg")
