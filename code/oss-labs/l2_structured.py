"""Lab 2, Exercise 1: schema-based output. Pydantic defines the shape; the model must return JSON that
matches it (Ollama supports JSON-schema structured outputs); code validates the result.
Run:  python l2_structured.py"""
from typing import Literal, Optional

from pydantic import BaseModel, Field

from client import CHAT_MODEL, get_client


class ProductRequest(BaseModel):
    need: str = Field(description="What the customer wants the product for, in a few words")
    family: Optional[Literal["accounts", "cards", "loans"]]
    max_annual_fee_usd: Optional[int] = Field(description="Highest annual fee in US dollars, or null")
    audience: Optional[Literal["personal", "student", "business"]]


REQUESTS = [
    "I'm a student and need a credit card to build my credit, no annual fee please.",
    "Looking for somewhere to keep my small company's tax money that earns some interest.",
    "Any card for travelling abroad? I could pay up to $100 a year.",
]
client = get_client()
for text in REQUESTS:
    completion = client.chat.completions.parse(
        model=CHAT_MODEL, temperature=0, response_format=ProductRequest,
        messages=[{"role": "system", "content": "Extract the customer's product request. Use null for anything not stated."},
                  {"role": "user", "content": text}])
    print(f"{text}\n  -> {completion.choices[0].message.parsed}\n")
