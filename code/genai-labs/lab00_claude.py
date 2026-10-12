"""Smoke test for the Claude track."""
from claude_llm import client, CLAUDE_MODEL, FALLBACK, text_of

response = client.beta.messages.create(
    model=CLAUDE_MODEL,
    max_tokens=4000,
    system="You are a friendly technical trainer.",
    messages=[{"role": "user", "content": "Greet a developer starting a GenAI course, in one sentence."}],
    **FALLBACK,
)
print(text_of(response))
print("tokens:", response.usage.input_tokens, "in /", response.usage.output_tokens, "out")
