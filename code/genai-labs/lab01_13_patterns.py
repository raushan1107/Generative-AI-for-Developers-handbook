"""Drill 01.13: let the model sort feature requests into GenAI patterns, then compare with your answers."""
from llm import get_client, MODEL

PATTERNS = ["generate", "transform", "extract", "search", "ground", "act", "not-genai"]

REQUESTS = [
    "Write a first draft of the course description from the trainer's bullet notes.",
    "Turn a 40-message support thread into a 3-line summary for the next agent.",
    "Pull the learner name, enrolment ID and course from incoming emails into our CRM.",
    "Let learners find courses by describing their goal, e.g. 'I want to automate Excel reports'.",
    "Answer 'Can I get a refund?' using the current policy document, with a citation.",
    "When a learner asks, look up their real exam voucher status and resend it.",
    "Calculate the refund amount from the cancellation date and course price.",
    "Translate course announcements into Spanish and Japanese.",
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
