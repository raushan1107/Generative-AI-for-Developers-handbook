"""Drill 06.1: closed book vs open book.
The same questions, first with only the model's own knowledge, then with the right help-centre
section pasted into the prompt by hand. That second version is RAG, done manually."""
import re
from pathlib import Path

from llm import MODEL, get_client

HELP = Path(__file__).parent / "data" / "help"
QUESTIONS = [
    ("How much do I get back if I cancel my TrainCrest course 10 days before it starts?",
     "refunds-and-cancellations", "How much you get back"),
    ("My TrainCrest lab shows error LAB-503. What should I do?", "labs-and-sandboxes", "Common problems"),
    ("How much does extra lab time cost at TrainCrest after the free extension?", "labs-and-sandboxes",
     "How long labs stay open"),
]


def section(article: str, heading: str) -> str:
    """Copy one section of a help article, the way you'd paste it into a chat by hand."""
    text = (HELP / f"{article}.md").read_text(encoding="utf-8")
    body = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text, re.M | re.S).group(1)
    return f"{heading}\n{body.strip()}"


def ask(messages):
    r = get_client().chat.completions.create(model=MODEL, messages=messages)
    return r.choices[0].message.content.strip()


for question, article, heading in QUESTIONS:
    closed = ask([{"role": "system", "content": "You are TrainCrest's learner-support assistant. Answer briefly."},
                  {"role": "user", "content": question}])
    context = section(article, heading)
    open_book = ask([{"role": "system", "content": "You are TrainCrest's learner-support assistant. Answer briefly, "
                                                   "using only the help-centre text provided. If it doesn't say, say so."},
                     {"role": "user", "content": f"<help>\n{context}\n</help>\n\nQuestion: {question}"}])
    print(f"Q: {question}\n\n  CLOSED BOOK: {closed}\n\n  OPEN BOOK:   {open_book}\n\n" + "-" * 80)
