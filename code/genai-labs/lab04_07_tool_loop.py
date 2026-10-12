"""Drill 04.7: the tool loop. Keep calling the model until it stops asking for tools,
with a hard limit on rounds. This loop is the heart of every assistant that "does things".
Run:  python lab04_07_tool_loop.py "Which advanced courses are under $1,400, and what does the cheapest cover?" """
import sys
from typing import Literal, Optional

from pydantic import BaseModel, Field

from catalogue import find_courses, get_course
from llm import MODEL, get_client
from llm_tools import TOOL_EXTRAS
from toolkit import Toolkit

kit = Toolkit()
MAX_ROUNDS = 5


class FindArgs(BaseModel):
    level: Optional[Literal["beginner", "intermediate", "advanced"]] = None
    max_price_usd: Optional[int] = None
    text: Optional[str] = Field(default=None, description="One keyword, e.g. 'azure'")


class CourseArgs(BaseModel):
    course_id: str = Field(description="Course ID such as C104")


@kit.register(FindArgs)
def search_courses(args):
    """Search the TrainCrest catalogue by level, maximum price or keyword."""
    return find_courses(level=args.level, max_price_usd=args.max_price_usd, text=args.text)


@kit.register(CourseArgs)
def course_details(args):
    """Full description, format and duration of one course."""
    return get_course(args.course_id) or {"error": f"no course {args.course_id}"}


def ask(question: str) -> str:
    client = get_client()
    messages = [{"role": "system", "content": "You are Traincrest Assist. Use tools for catalogue facts. Be brief."},
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
    q = sys.argv[1] if len(sys.argv) > 1 else "Which advanced courses are under $1,400, and what does the cheapest cover?"
    print("Q:", q)
    print("A:", ask(q))
