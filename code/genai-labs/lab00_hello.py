"""Smoke test: prove the pipe from your laptop to the model works."""
from llm import get_client, MODEL, PROVIDER

client = get_client()
response = client.chat.completions.create(
    model=MODEL,
    messages=[{"role": "user", "content": "Greet a developer starting a GenAI course, in one sentence."}],
)

print(f"[{PROVIDER} · {MODEL}]")
print(response.choices[0].message.content)
print("tokens:", response.usage.prompt_tokens, "in /", response.usage.completion_tokens, "out")
