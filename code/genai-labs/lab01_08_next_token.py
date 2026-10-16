"""Drill 01.8: the real probability distribution behind one token, and sampling in action."""
import math

import openai

from llm import get_client, MODEL

client = get_client()

# Part A: what were the candidates for the first token?
try:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": "Complete with one word only: The currency of Japan is the"}],
        logprobs=True,     # return the log-probability of each generated token
        top_logprobs=5,    # ...and the top 5 alternatives at each position
    )
    lp = response.choices[0].logprobs
    if lp is None or not lp.content:
        raise ValueError("no logprobs returned")
    first = lp.content[0]
    print(f"Chosen first token: {first.token!r}\n")
    for cand in first.top_logprobs:
        pct = math.exp(cand.logprob) * 100
        print(f"  {cand.token!r:14} {pct:6.2f}%  {'#' * round(pct / 4)}")
except (openai.BadRequestError, ValueError) as err:
    print("This model doesn't return token probabilities:", err)

# Part B: the same open-ended prompt, three times
print("\nThree samples of the same prompt:")
for i in range(3):
    r = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": "Invent a 4-word slogan for a digital savings account. Slogan only."}],
    )
    print(f"  {i + 1}. {r.choices[0].message.content.strip()}")
