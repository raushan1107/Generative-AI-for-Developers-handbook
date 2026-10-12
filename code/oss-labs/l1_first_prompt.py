"""Lab 1, Exercise 1: send a prompt to an open-source model and display the response.
Run:  python l1_first_prompt.py "Explain what a large language model is in two sentences." """
import sys
import time

from client import CHAT_MODEL, get_client

prompt = sys.argv[1] if len(sys.argv) > 1 else "Explain what a large language model is in two sentences."

start = time.perf_counter()
response = get_client().chat.completions.create(
    model=CHAT_MODEL,
    messages=[{"role": "user", "content": prompt}],
)
seconds = time.perf_counter() - start

print(f"Prompt : {prompt}")
print(f"Answer : {response.choices[0].message.content.strip()}")
print(f"Model  : {response.model} · {seconds:.1f}s · "
      f"{response.usage.prompt_tokens} tokens in, {response.usage.completion_tokens} tokens out · cost $0 (local)")
