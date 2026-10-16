"""Drill 04.3: structured outputs. A Pydantic model becomes a strict JSON Schema,
the model is constrained to it, and the SDK hands back a typed object.
Run:  python lab04_03_schema.py --show-schema   (offline: print the schema the API receives)
      python lab04_03_schema.py                 (live: triage the same five messages)"""
import json
import sys
from typing import Literal, Optional

import openai
from pydantic import BaseModel, Field

from lab04_02_json_mode import MESSAGES


class Triage(BaseModel):
    customer_name: Optional[str] = Field(description="First name if given, else null")
    customer_id: Optional[str] = Field(description="Like RR-12345. Null if not given. Never invent one.")
    category: Literal["card", "dispute", "fraud", "fees", "transfers", "loans", "account", "other"]
    urgent: bool = Field(description="True for fraud, a lost or stolen card, or a deadline within 3 days")
    summary: str = Field(description="One English sentence, at most 20 words")


SYSTEM = ("You triage RR Finance Bank customer messages. A payment the customer recognises but that is wrong "
          "is dispute; a payment they don't recognise is fraud; asking for a fee back is fees.")


def show_schema():
    # pydantic_function_tool builds the same strict schema that .parse() sends.
    schema = openai.pydantic_function_tool(Triage)["function"]["parameters"]
    print(json.dumps(schema, indent=2))


def main():
    from llm import MODEL, get_client
    client = get_client()
    for text in MESSAGES:
        completion = client.chat.completions.parse(
            model=MODEL,
            messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": text}],
            response_format=Triage,              # the SDK converts the class to a strict json_schema
        )
        message = completion.choices[0].message
        if message.refusal:                      # safety refusals come back here, not as JSON
            print("REFUSED:", message.refusal)
            continue
        t: Triage = message.parsed               # a real Triage object, already validated
        print(f"{t.category:<10} urgent={t.urgent!s:<5} id={t.customer_id}  {t.summary}")


if __name__ == "__main__":
    show_schema() if "--show-schema" in sys.argv else main()
