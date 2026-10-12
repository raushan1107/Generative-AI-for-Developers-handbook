"""Drill 01.3: a classic ML classifier vs an LLM, on the same support tickets."""
import json
import time
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

from llm import get_client, MODEL
from tickets import CATEGORIES, TEST_TICKETS

# ---------- 1) Classic ML: learn from labelled examples ----------
train = json.loads(Path("data/train_tickets.json").read_text(encoding="utf-8"))
texts = [t["text"] for t in train]
labels = [t["label"] for t in train]

start = time.perf_counter()
classifier = make_pipeline(TfidfVectorizer(ngram_range=(1, 2)), LogisticRegression(max_iter=1000))
classifier.fit(texts, labels)
train_secs = time.perf_counter() - start

start = time.perf_counter()
ml_preds = list(classifier.predict([text for text, _ in TEST_TICKETS]))
ml_secs = time.perf_counter() - start

# ---------- 2) LLM: no training, just an instruction ----------
client = get_client()
instruction = f"Classify the support ticket into one of: {', '.join(CATEGORIES)}. Reply with the category only."
llm_preds, tokens = [], 0
start = time.perf_counter()
for text, _ in TEST_TICKETS:
    r = client.chat.completions.create(model=MODEL, messages=[
        {"role": "system", "content": instruction},
        {"role": "user", "content": text},
    ])
    llm_preds.append(r.choices[0].message.content.strip().lower())
    tokens += r.usage.total_tokens
llm_secs = time.perf_counter() - start

# ---------- 3) Compare ----------
print(f"{'ticket':46} {'expected':13} {'classic ML':13} {'LLM':13}")
for (text, expected), ml, llm in zip(TEST_TICKETS, ml_preds, llm_preds):
    print(f"{text[:44]:46} {expected:13} {ml:13} {llm:13}")

n = len(TEST_TICKETS)
ml_ok = sum(p == e for p, (_, e) in zip(ml_preds, TEST_TICKETS))
llm_ok = sum(p == e for p, (_, e) in zip(llm_preds, TEST_TICKETS))
print(f"\nClassic ML: {ml_ok}/{n} correct · trained in {train_secs:.2f}s on {len(train)} examples · "
      f"all predictions in {ml_secs * 1000:.1f} ms · $0 per call")
print(f"LLM:        {llm_ok}/{n} correct · no training · {llm_secs:.1f}s for all · {tokens} tokens")
