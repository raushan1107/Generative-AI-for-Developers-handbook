"""Drill 04.7: the tool loop. Keep calling the model until it stops asking for tools,
with a hard limit on rounds. This loop is the heart of every assistant that "does things".
Run:  python lab04_07_tool_loop.py "Which cards have no annual fee, and what does the one with the lowest APR offer?" """
import sys
from typing import Literal, Optional

from pydantic import BaseModel, Field

from catalogue import find_products, get_product
from llm import MODEL, get_client
from llm_tools import TOOL_EXTRAS
from toolkit import Toolkit

kit = Toolkit()
MAX_ROUNDS = 5


class FindArgs(BaseModel):
    family: Optional[Literal["accounts", "cards", "loans"]] = None
    audience: Optional[Literal["personal", "student", "business"]] = None
    max_annual_fee_usd: Optional[int] = None
    text: Optional[str] = Field(default=None, description="One keyword, e.g. 'travel'")


class ProductArgs(BaseModel):
    product_id: str = Field(description="Product ID such as P110")


@kit.register(FindArgs)
def search_products(args):
    """Search the RR Finance Bank catalogue by family, audience, maximum annual fee or keyword."""
    return find_products(family=args.family, audience=args.audience,
                         max_annual_fee_usd=args.max_annual_fee_usd, text=args.text)


@kit.register(ProductArgs)
def product_details(args):
    """Full description, fee and rate of one product."""
    return get_product(args.product_id) or {"error": f"no product {args.product_id}"}


def ask(question: str) -> str:
    client = get_client()
    messages = [{"role": "system", "content": "You are RR Finance Assist. Use tools for product facts. "
                                              "Explain products; don't recommend what to buy. Be brief."},
                {"role": "user", "content": question}]
    for round_no in range(1, MAX_ROUNDS + 1):
        r = client.chat.completions.create(model=MODEL, messages=messages, tools=kit.schemas(),
                                           parallel_tool_calls=False, **TOOL_EXTRAS)
        msg = r.choices[0].message
        if not msg.tool_calls:                       # no more tools wanted: this is the answer
            return msg.content
        messages.append(msg)
        for call in msg.tool_calls:
            result = kit.dispatch(call.function.name, call.function.arguments)
            print(f"  round {round_no}: {call.function.name}({call.function.arguments}) -> {result[:80]}...")
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
    return "Sorry, I couldn't finish that. Please ask a simpler question."   # loop limit reached


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "Which cards have no annual fee, and what does the one with the lowest APR offer?"
    print("Q:", q)
    print("A:", ask(q))
