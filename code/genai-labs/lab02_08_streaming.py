"""Drill 02.8: streaming. Time to first token vs total time."""
import time

from llm import get_client, MODEL

client = get_client()
messages = [{"role": "user", "content": "Write a 150-word guide to building an emergency fund."}]

# A) Wait for the whole answer
start = time.perf_counter()
client.chat.completions.create(model=MODEL, messages=messages)
print(f"Without streaming: blank screen for {time.perf_counter() - start:.1f}s, then everything at once.\n")

# B) Stream it
start, ttft, chunks, usage = time.perf_counter(), None, 0, None
stream = client.chat.completions.create(
    model=MODEL, messages=messages,
    stream=True, stream_options={"include_usage": True},
)
for chunk in stream:
    if chunk.usage:                 # the last chunk carries token usage
        usage = chunk.usage
    if not chunk.choices:           # some chunks carry no text (filter results, usage)
        continue
    delta = chunk.choices[0].delta.content
    if delta:
        if ttft is None:
            ttft = time.perf_counter() - start
        chunks += 1
        print(delta, end="", flush=True)

total = time.perf_counter() - start
print(f"\n\nWith streaming: first words after {ttft:.1f}s, done after {total:.1f}s, {chunks} chunks.")
if usage:
    print(f"Usage: {usage.prompt_tokens} in / {usage.completion_tokens} out")
