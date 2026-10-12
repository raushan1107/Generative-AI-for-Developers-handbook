"""Drill 02.10: break it on purpose and read the errors."""
import openai
from openai import OpenAI

from llm import get_client, MODEL

good = get_client()
hello = [{"role": "user", "content": "Hello"}]


def attempt(label, fn):
    try:
        fn()
        print(f"{label:30} OK")
    except openai.APIStatusError as e:          # the server answered with an error status
        print(f"{label:30} {type(e).__name__} (HTTP {e.status_code}): {str(e.message)[:70]}")
    except openai.APIConnectionError as e:      # no usable answer at all (includes timeouts)
        print(f"{label:30} {type(e).__name__}: {e}")


attempt("1. Wrong API key", lambda: OpenAI(base_url=good.base_url, api_key="wrong", max_retries=0)
        .chat.completions.create(model=MODEL, messages=hello))
attempt("2. Wrong deployment name", lambda: good.chat.completions.create(model="no-such-deployment", messages=hello))
attempt("3. Invalid parameter value", lambda: good.chat.completions.create(model=MODEL, messages=hello, temperature=5))
attempt("4. Unreachable endpoint", lambda: OpenAI(base_url="http://localhost:9/v1", api_key="x", max_retries=0)
        .chat.completions.create(model=MODEL, messages=hello))
attempt("5. Impossible timeout", lambda: good.with_options(timeout=0.001, max_retries=0)
        .chat.completions.create(model=MODEL, messages=hello))

# 6) Not an exception, but still a failure
r = good.chat.completions.create(model=MODEL, max_completion_tokens=30,
                                 messages=[{"role": "user", "content": "Write a long essay about cloud computing."}])
print(f"{'6. Truncated answer':30} HTTP 200, finish_reason={r.choices[0].finish_reason!r}")
