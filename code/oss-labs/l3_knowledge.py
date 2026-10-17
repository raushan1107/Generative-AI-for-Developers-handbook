"""Lab 3, Exercise 1: a Company Knowledge Assistant (RAG) that answers questions from RR Finance Bank's own
documents, public help articles and internal staff documents, and cites its sources.
Run:  python l3_knowledge.py            (customer view: help centre only)
      python l3_knowledge.py --staff    (staff view: help centre + internal documents)"""
import csv
import json
import re
import sys
from pathlib import Path

import numpy as np

from client import CHAT_MODEL, EMBED_MODEL, get_client, get_embed_client

DATA = Path(__file__).parent / "data"
INDEX = DATA / "kb_index.json"
MIN_SCORE = 0.55          # relevance floor for nomic-embed-text; other embedding models need their own value
NOT_FOUND = "NOT_FOUND"


# ---------------- 1. ingest: every format becomes "# Title" + "## Section" text
def read_document(path: Path) -> str:
    if path.suffix == ".csv":                                   # question,answer rows
        rows = list(csv.DictReader(path.open(encoding="utf-8")))
        return f"# {path.stem.replace('-', ' ').title()}\n" + "\n".join(f"## {r['question']}\n{r['answer']}" for r in rows)
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".txt":                                   # UPPER-CASE lines are headings
        lines = text.splitlines()
        return f"# {lines[0].title()}\n" + "\n".join(f"## {l.capitalize()}" if l.isupper() else l for l in lines[1:])
    return text


# ---------------- 2. chunk: one chunk per section, intro included, title on every chunk
def chunks(path: Path, audience: str):
    text = read_document(path)
    title = re.search(r"^# (.+)$", text, re.M).group(1).strip()
    intro, *parts = re.split(r"^## ", re.sub(r"^# .+\n", "", text, count=1), flags=re.M)
    sections = ([("Overview", intro)] if intro.strip() else []) + [p.partition("\n")[::2] for p in parts]
    for heading, body in sections:
        yield {"title": f"{title} > {heading.strip()}", "source": path.name, "audience": audience,
               "text": f"{title} > {heading.strip()}\n{body.strip()}"}


def embed(texts):
    data = get_embed_client().embeddings.create(model=EMBED_MODEL, input=texts).data
    v = np.array([d.embedding for d in data])
    return v / np.linalg.norm(v, axis=1, keepdims=True)


# ---------------- 3. embed and store (once; rebuilt if the embedding model changes)
def load_index():
    if INDEX.exists():
        saved = json.loads(INDEX.read_text(encoding="utf-8"))
        if saved["model"] == EMBED_MODEL:
            return saved["chunks"], np.array(saved["vectors"])
    items = [c for folder, audience in (("help", "public"), ("internal", "staff"))
             for path in sorted((DATA / folder).iterdir()) for c in chunks(path, audience)]
    vectors = embed([c["text"] for c in items])
    INDEX.write_text(json.dumps({"model": EMBED_MODEL, "chunks": items, "vectors": vectors.tolist()}), encoding="utf-8")
    return items, vectors


# ---------------- 4. retrieve: only what this audience may see, only above the floor
def retrieve(question, items, vectors, audience, k=4):
    allowed = [i for i, c in enumerate(items) if c["audience"] in audience]
    scores = vectors[allowed] @ embed([question])[0]
    best = [allowed[j] for j in np.argsort(-scores)[:k] if scores[j] >= MIN_SCORE]
    return [items[i] for i in best]


# ---------------- 5 and 6. build the prompt, generate, check citations
def answer(question, items, vectors, audience):
    sources = retrieve(question, items, vectors, audience)
    if not sources:
        return "I couldn't find that in RR Finance Bank's documents.", []
    blocks = "\n\n".join(f'<source id="{n}">\n{s["text"]}\n</source>' for n, s in enumerate(sources, 1))
    system = ("Answer using ONLY the numbered sources. After each fact, cite its source number like [1]. "
              f"If the sources don't answer the question, reply exactly {NOT_FOUND}. Answer in the question's language.")
    reply = get_client().chat.completions.create(model=CHAT_MODEL, temperature=0, messages=[
        {"role": "system", "content": system},
        {"role": "user", "content": f"<sources>\n{blocks}\n</sources>\n\nQuestion: {question}"}]).choices[0].message.content
    if NOT_FOUND in reply:
        return "I couldn't find that in RR Finance Bank's documents.", []
    cited = sorted({int(n) for n in re.findall(r"\[(\d+)\]", reply) if 1 <= int(n) <= len(sources)})
    reply = re.sub(r"\[(\d+)\]", lambda m: m.group(0) if int(m.group(1)) in cited else "", reply)  # drop invented ones
    return reply.strip(), [(n, sources[n - 1]) for n in cited]


if __name__ == "__main__":
    audience = ("public", "staff") if "--staff" in sys.argv else ("public",)
    items, vectors = load_index()
    print(f"RR Finance Bank knowledge assistant ({'staff' if len(audience) == 2 else 'customer'} view). Empty line to quit.\n")
    while question := input("Question: ").strip():
        text, cited = answer(question, items, vectors, audience)
        print(text)
        for n, s in cited:
            print(f"  [{n}] {s['title']} ({s['source']})")
        print()
