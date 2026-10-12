"""Drill 01.11: one prompt, several models. Compare latency, tokens and quality."""
import os
import time

from openai import OpenAI

from llm import get_client, MODEL

targets = [("main", get_client(), MODEL)]
if os.getenv("COMPARE_DEPLOYMENT"):
    targets.append(("compare", get_client(), os.environ["COMPARE_DEPLOYMENT"]))
if os.getenv("COMPARE_WITH_OLLAMA") == "1":
    local = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
    targets.append(("local", local, os.getenv("OLLAMA_MODEL", "llama3.2")))

PROMPT = ("A learner writes: 'My course starts in 5 days but I have a family emergency. "
          "I want my full $1,200 back!!' TrainCrest's policy: no refund within 7 days of the start "
          "date, but one free reschedule. Reply as a kind support agent in under 80 words.")

for label, client, model in targets:
    start = time.perf_counter()
    r = client.chat.completions.create(model=model, messages=[{"role": "user", "content": PROMPT}])
    secs = time.perf_counter() - start
    u = r.usage
    print(f"\n=== {label} · {model} · {secs:.1f}s · {u.prompt_tokens} in / {u.completion_tokens} out")
    print(r.choices[0].message.content.strip())
