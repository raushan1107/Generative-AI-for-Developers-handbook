"""Drill 04.6: which tool does the model pick, and how do you steer it?
Run:  python lab04_06_tool_choice.py                 (tool_choice="auto")
      python lab04_06_tool_choice.py none            (never call a tool)
      python lab04_06_tool_choice.py required        (must call some tool)
      python lab04_06_tool_choice.py get_product     (must call this one)
      python lab04_06_tool_choice.py auto --parallel (allow several calls in one turn)"""
import json
import sys
from typing import Literal, Optional

import openai
from pydantic import BaseModel, Field

from llm import MODEL, get_client
from llm_tools import TOOL_EXTRAS


class FindProducts(BaseModel):
    """Search the product catalogue by family, audience, annual fee or keyword."""
    family: Optional[Literal["accounts", "cards", "loans"]] = None
    audience: Optional[Literal["personal", "student", "business"]] = None
    max_annual_fee_usd: Optional[int] = None
    text: Optional[str] = None


class GetProduct(BaseModel):
    """Full details of one product by its ID, like P110."""
    product_id: str = Field(description="Product ID such as P110")


class GetCardStatus(BaseModel):
    """Status of one of the signed-in customer's cards: active, frozen, replacement sent."""
    card_last4: str = Field(description="Last four digits of the card, like 4821")


QUESTIONS = [
    "What does P111 offer?",
    "Has the replacement for my card ending 4821 been sent?",
    "Compare P104 and P106 for me.",
    "Thanks, that's all!",
]

choice = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "auto"
parallel = "--parallel" in sys.argv
tools = [openai.pydantic_function_tool(FindProducts, name="find_products"),
         openai.pydantic_function_tool(GetProduct, name="get_product"),
         openai.pydantic_function_tool(GetCardStatus, name="get_card_status")]
if parallel:
    for t in tools:                    # strict tools can't be combined with parallel calls
        t["function"]["strict"] = False
tool_choice = choice if choice in ("auto", "none", "required") else {"type": "function", "function": {"name": choice}}

client = get_client()
print(f"tool_choice={choice}  parallel_tool_calls={parallel}\n")
for q in QUESTIONS:
    r = client.chat.completions.create(
        model=MODEL, messages=[{"role": "user", "content": q}], tools=tools,
        tool_choice=tool_choice, parallel_tool_calls=parallel, **TOOL_EXTRAS)
    calls = r.choices[0].message.tool_calls or []
    picked = ", ".join(f"{c.function.name}({json.loads(c.function.arguments)})" for c in calls) or "no tool (text answer)"
    print(f"{q:<42} -> {picked}")
