"""Lab 2, Exercise 1: schema-based output. Pydantic defines the shape; the model must return JSON that
matches it (Ollama supports JSON-schema structured outputs); code validates the result.
Run:  python l2_structured.py"""
from typing import Literal, Optional

from pydantic import BaseModel, Field

from client import CHAT_MODEL, get_client


class CourseRequest(BaseModel):
    topic: str = Field(description="What the learner wants to learn, in a few words")
    level: Optional[Literal["beginner", "intermediate", "advanced"]]
    max_price_usd: Optional[int] = Field(description="Budget in US dollars, or null")
    format: Optional[Literal["live-online", "classroom", "self-paced"]]


REQUESTS = [
    "I'm new to the cloud and want something on Azure basics, under 400 dollars please.",
    "Looking for an advanced course on building RAG apps, online with a trainer.",
    "Any self-paced Python course? Budget is about $300.",
]
client = get_client()
for text in REQUESTS:
    completion = client.chat.completions.parse(
        model=CHAT_MODEL, temperature=0, response_format=CourseRequest,
        messages=[{"role": "system", "content": "Extract the learner's course request. Use null for anything not stated."},
                  {"role": "user", "content": text}])
    print(f"{text}\n  -> {completion.choices[0].message.parsed}\n")
