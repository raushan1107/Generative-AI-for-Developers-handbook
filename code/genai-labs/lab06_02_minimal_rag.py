"""Drill 06.2: the smallest RAG that works, every stage in plain sight.
Index (ahead of time): load the help articles, chunk them by heading, embed the chunks.
Query (every question): embed the question, take the 3 nearest chunks, put them in the prompt, generate.
Run:  python lab06_02_minimal_rag.py "How much is the fee for an international wire?" """
import re
import sys
import time
from pathlib import Path

import numpy as np

from embed import embed
from llm import MODEL, get_client

question = sys.argv[1] if len(sys.argv) > 1 else "How much is the fee for an international wire?"
clock = time.perf_counter()


def stage(name):
    global clock
    now = time.perf_counter()
    print(f"[{now - clock:5.2f}s] {name}")
    clock = now


# ---- INDEXING: ahead of time, once per content change
chunks = []
for path in sorted((Path(__file__).parent / "data" / "help").glob("*.md")):
    text = path.read_text(encoding="utf-8")
    title = re.search(r"^# (.+)$", text, re.M).group(1)
    for part in re.split(r"^## ", text, flags=re.M)[1:]:
        heading, _, body = part.partition("\n")
        chunks.append({"source": f"{path.stem} > {heading.strip()}", "text": f"{title} > {heading}\n{body.strip()}"})
stage(f"ingest + chunk: {len(chunks)} chunks")
vectors = embed([c["text"] for c in chunks])
vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)
stage(f"embed + store: {vectors.shape[0]} vectors of {vectors.shape[1]} numbers")

# ---- QUERY: every question
q = embed([question])[0]
scores = vectors @ (q / np.linalg.norm(q))
top = np.argsort(-scores)[:3]
stage("retrieve: " + ", ".join(f"{chunks[i]['source']} ({scores[i]:.2f})" for i in top))
context = "\n\n".join(f"[{n}] {chunks[i]['text']}" for n, i in enumerate(top, start=1))
messages = [{"role": "system", "content": "Answer using only the numbered sources. Cite them like [1]. "
                                          "If they don't contain the answer, say you don't know."},
            {"role": "user", "content": f"{context}\n\nQuestion: {question}"}]
stage("prompt: question + 3 sources")
answer = get_client().chat.completions.create(model=MODEL, messages=messages).choices[0].message.content
stage("generate")
print(f"\nQ: {question}\nA: {answer.strip()}")
