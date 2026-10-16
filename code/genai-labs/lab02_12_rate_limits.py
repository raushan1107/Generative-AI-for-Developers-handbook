"""Drill 02.12: rate-limit headers, a real 429, and exponential backoff with jitter."""
import random
import time

import openai

from llm import get_client, MODEL

client = get_client().with_options(max_retries=0)   # SDK retries off, so we see the 429s

# A) How much budget is left? Read the headers.
raw = client.chat.completions.with_raw_response.create(
    model=MODEL, messages=[{"role": "user", "content": "Hi"}])
for h in ("x-ratelimit-limit-tokens", "x-ratelimit-remaining-tokens",
          "x-ratelimit-limit-requests", "x-ratelimit-remaining-requests"):
    print(f"{h}: {raw.headers.get(h)}")
raw.parse()   # the normal response object is still available


# B) Our own retry loop
def call_with_backoff(messages, max_attempts=6, base=1.0, cap=30.0):
    for attempt in range(1, max_attempts + 1):
        try:
            return client.chat.completions.create(model=MODEL, messages=messages)
        except (openai.RateLimitError, openai.InternalServerError, openai.APIConnectionError) as e:
            if attempt == max_attempts:
                raise
            response = getattr(e, "response", None)
            retry_after = response.headers.get("retry-after") if response is not None else None
            wait = float(retry_after) if retry_after else min(cap, base * 2 ** (attempt - 1))
            wait += random.uniform(0, wait * 0.25)   # jitter: don't retry in lockstep
            print(f"   attempt {attempt}: {type(e).__name__}, waiting {wait:.1f}s")
            time.sleep(wait)


# C) Spend the budget fast to trigger 429s
print()
for i in range(12):
    r = call_with_backoff([{"role": "user", "content": "Write 150 words about how credit scores work."}])
    print(f"request {i + 1:2} ok · {r.usage.total_tokens} tokens")
