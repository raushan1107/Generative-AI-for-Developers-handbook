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

PROMPT = ("A customer writes: 'You charged me a $29 overdraft fee! I was only $80 short for one night "
          "because my salary was late. Give it back now!!' RR Finance Bank's policy: $29 fee when overdrawn by "
          "more than $50 at the end of the day; one courtesy fee refund per account every 12 months, and this "
          "customer hasn't used it. Reply as a kind contact-centre agent in under 80 words.")

for label, client, model in targets:
    start = time.perf_counter()
    r = client.chat.completions.create(model=model, messages=[{"role": "user", "content": PROMPT}])
    secs = time.perf_counter() - start
    u = r.usage
    print(f"\n=== {label} · {model} · {secs:.1f}s · {u.prompt_tokens} in / {u.completion_tokens} out")
    print(r.choices[0].message.content.strip())
