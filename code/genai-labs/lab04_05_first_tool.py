"""Drill 04.5: your first function call, one step at a time.
The model never runs code. It asks YOU to run a function; you send back the result."""
import json
from typing import Literal, Optional

import openai
from pydantic import BaseModel, Field

from catalogue import find_products
from llm import MODEL, get_client
from llm_tools import TOOL_EXTRAS


class FindProducts(BaseModel):
    """Search the RR Finance Bank product catalogue. Use it for any question about accounts, cards, loans, fees or rates."""
    family: Optional[Literal["accounts", "cards", "loans"]] = None
    audience: Optional[Literal["personal", "student", "business"]] = None
    max_annual_fee_usd: Optional[int] = Field(default=None, description="Highest annual fee the customer will pay, in USD")
    text: Optional[str] = Field(default=None, description="One keyword to look for in names and descriptions, e.g. 'travel'")


TOOLS = [openai.pydantic_function_tool(FindProducts, name="find_products")]


def main():
    client = get_client()
    messages = [
        {"role": "system", "content": "You are RR Finance Assist. Use tools for product facts; never guess fees or rates."},
        {"role": "user", "content": "Do you have a credit card with no annual fee for students?"},
    ]

    # Step 1: send the question AND the tool descriptions.
    first = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS, **TOOL_EXTRAS)
    msg = first.choices[0].message
    print("1) finish_reason:", first.choices[0].finish_reason)
    if not msg.tool_calls:
        print("The model answered without a tool:", msg.content)
        return

    # Step 2: the model asked for a call. Run it ourselves.
    messages.append(msg)                          # the assistant turn that contains tool_calls
    for call in msg.tool_calls:
        print(f"2) model asks: {call.function.name}({call.function.arguments})")
        # Validate before you call: strict mode guarantees the shape on Azure/OpenAI, but not every
        # provider enforces it, and a model can still send values your function can't use.
        args = FindProducts.model_validate_json(call.function.arguments)
        result = find_products(**args.model_dump())
        print(f"   we ran it:  {len(result)} result(s)")
        messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)})

    # Step 3: send the results back; the model writes the final answer.
    final = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS, **TOOL_EXTRAS)
    print("3) answer:", final.choices[0].message.content)


if __name__ == "__main__":
    main()
