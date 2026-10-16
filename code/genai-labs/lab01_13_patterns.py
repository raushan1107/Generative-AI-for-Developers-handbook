"""Drill 01.13: let the model sort feature requests into GenAI patterns, then compare with your answers."""
from llm import get_client, MODEL

PATTERNS = ["generate", "transform", "extract", "search", "ground", "act", "not-genai"]

REQUESTS = [
    "Write a first draft of the new savings account's web page from the product team's bullet notes.",
    "Turn a 40-message complaint thread into a 3-line summary for the next agent.",
    "Pull the customer name, customer ID and disputed amount from incoming emails into the case system.",
    "Let customers find the right account by describing their goal, e.g. 'I want to save for a house deposit'.",
    "Answer 'Can I get my overdraft fee back?' using the current fee policy, with a citation.",
    "When a customer asks, look up the real status of their card and freeze it.",
    "Calculate the monthly payment on a $15,000 loan at 7.99% APR over 36 months.",
    "Translate fraud warning messages into Spanish and Japanese.",
]

client = get_client()
system = (f"Classify each feature request into exactly one pattern from: {', '.join(PATTERNS)}. "
          "'ground' means answering from specific documents; 'act' means calling a system or tool; "
          "'not-genai' means plain code does it better. Reply with one line per request: number, pattern, "
          "and a reason of at most 12 words.")
numbered = "\n".join(f"{i}. {r}" for i, r in enumerate(REQUESTS, 1))
r = client.chat.completions.create(model=MODEL, messages=[
    {"role": "system", "content": system},
    {"role": "user", "content": numbered},
])
print(r.choices[0].message.content.strip())
