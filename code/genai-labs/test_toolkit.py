"""Drill 04.7: the spec for toolkit.py. Ask your AI assistant to make these pass.
Run:  pytest -q test_toolkit.py"""
import json
from typing import Optional

from pydantic import BaseModel

from toolkit import Toolkit

kit = Toolkit()


class PriceArgs(BaseModel):
    course_id: str


class MyEnrolmentArgs(BaseModel):
    status: Optional[str]


@kit.register(PriceArgs)
def get_price(args):
    """Price of a course in USD."""
    if args.course_id == "BOOM":
        raise RuntimeError("database down")
    return {"course_id": args.course_id, "price_usd": 1490}


@kit.register(MyEnrolmentArgs, needs_context=True)
def my_enrolments(args, context):
    """Enrolments of the signed-in learner."""
    return {"learner": context["learner_id"], "status": args.status}


def test_schemas_are_strict_function_tools():
    names = {t["function"]["name"]: t["function"] for t in kit.schemas()}
    assert set(names) == {"get_price", "my_enrolments"}
    assert names["get_price"]["strict"] is True
    assert names["get_price"]["description"] == "Price of a course in USD."


def test_dispatch_runs_the_function():
    assert json.loads(kit.dispatch("get_price", '{"course_id": "C104"}')) == {"course_id": "C104", "price_usd": 1490}


def test_context_comes_from_the_app_not_the_model():
    out = json.loads(kit.dispatch("my_enrolments", '{"status": null}', context={"learner_id": "L-MEI"}))
    assert out["learner"] == "L-MEI"


def test_problems_become_error_messages_not_crashes():
    assert "unknown tool" in json.loads(kit.dispatch("delete_everything", "{}"))["error"]
    assert "invalid arguments" in json.loads(kit.dispatch("get_price", '{"id": "C104"}'))["error"]
    assert "invalid arguments" in json.loads(kit.dispatch("get_price", '{"course_id": '))["error"]
    assert json.loads(kit.dispatch("get_price", '{"course_id": "BOOM"}')) == {"error": "tool failed: RuntimeError"}
