"""Drill 04.6: which tool does the model pick, and how do you steer it?
Run:  python lab04_06_tool_choice.py                 (tool_choice="auto")
      python lab04_06_tool_choice.py none            (never call a tool)
      python lab04_06_tool_choice.py required        (must call some tool)
      python lab04_06_tool_choice.py get_course      (must call this one)
      python lab04_06_tool_choice.py auto --parallel (allow several calls in one turn)"""
import json
import sys
from typing import Literal, Optional

import openai
from pydantic import BaseModel, Field

from llm import MODEL, get_client
from llm_tools import TOOL_EXTRAS


class FindCourses(BaseModel):
    """Search the catalogue by level, budget or keyword."""
    level: Optional[Literal["beginner", "intermediate", "advanced"]] = None
    max_price_usd: Optional[int] = None
    text: Optional[str] = None


class GetCourse(BaseModel):
    """Full details of one course by its ID, like C104."""
    course_id: str = Field(description="Course ID such as C104")


class GetVoucherStatus(BaseModel):
    """Exam voucher status for the signed-in learner's enrolment."""
    enrolment_id: str = Field(description="Like TC-12345")


QUESTIONS = [
    "What does C104 cover?",
    "Has my voucher for TC-10293 been issued?",
    "Compare C110 and C111 for me.",
    "Thanks, that's all!",
]

choice = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "auto"
parallel = "--parallel" in sys.argv
tools = [openai.pydantic_function_tool(FindCourses, name="find_courses"),
         openai.pydantic_function_tool(GetCourse, name="get_course"),
         openai.pydantic_function_tool(GetVoucherStatus, name="get_voucher_status")]
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
