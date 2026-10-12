"""Drill 04.5: your first function call, one step at a time.
The model never runs code. It asks YOU to run a function; you send back the result."""
import json
from typing import Literal, Optional

import openai
from pydantic import BaseModel, Field

from catalogue import find_courses
from llm import MODEL, get_client
from llm_tools import TOOL_EXTRAS


class FindCourses(BaseModel):
    """Search the TrainCrest catalogue. Use it for any question about courses, levels or prices."""
    level: Optional[Literal["beginner", "intermediate", "advanced"]] = None
    max_price_usd: Optional[int] = Field(default=None, description="Highest price the learner will pay, in USD")
    text: Optional[str] = Field(default=None, description="One keyword to look for in titles and descriptions, e.g. 'python'")


TOOLS = [openai.pydantic_function_tool(FindCourses, name="find_courses")]


def main():
    client = get_client()
    messages = [
        {"role": "system", "content": "You are Traincrest Assist. Use tools for catalogue facts; never guess prices."},
        {"role": "user", "content": "Is there a beginner Python course under $300?"},
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
        args = FindCourses.model_validate_json(call.function.arguments)
        result = find_courses(**args.model_dump())
        print(f"   we ran it:  {len(result)} result(s)")
        messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)})

    # Step 3: send the results back; the model writes the final answer.
    final = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS, **TOOL_EXTRAS)
    print("3) answer:", final.choices[0].message.content)


if __name__ == "__main__":
    main()
