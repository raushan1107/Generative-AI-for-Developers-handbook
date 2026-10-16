"""Drill 04.7: the spec for toolkit.py. Ask your AI assistant to make these pass.
Run:  pytest -q test_toolkit.py"""
import json
from typing import Optional

from pydantic import BaseModel

from toolkit import Toolkit

kit = Toolkit()


class RateArgs(BaseModel):
    product_id: str


class MyAccountArgs(BaseModel):
    status: Optional[str]


@kit.register(RateArgs)
def get_rate(args):
    """Interest rate of a product, in percent."""
    if args.product_id == "BOOM":
        raise RuntimeError("database down")
    return {"product_id": args.product_id, "rate_pct": 22.99}


@kit.register(MyAccountArgs, needs_context=True)
def my_accounts(args, context):
    """Accounts of the signed-in customer."""
    return {"customer": context["customer_id"], "status": args.status}


def test_schemas_are_strict_function_tools():
    names = {t["function"]["name"]: t["function"] for t in kit.schemas()}
    assert set(names) == {"get_rate", "my_accounts"}
    assert names["get_rate"]["strict"] is True
    assert names["get_rate"]["description"] == "Interest rate of a product, in percent."


def test_dispatch_runs_the_function():
    assert json.loads(kit.dispatch("get_rate", '{"product_id": "P110"}')) == {"product_id": "P110", "rate_pct": 22.99}


def test_context_comes_from_the_app_not_the_model():
    out = json.loads(kit.dispatch("my_accounts", '{"status": null}', context={"customer_id": "RR-10293"}))
    assert out["customer"] == "RR-10293"


def test_problems_become_error_messages_not_crashes():
    assert "unknown tool" in json.loads(kit.dispatch("delete_everything", "{}"))["error"]
    assert "invalid arguments" in json.loads(kit.dispatch("get_rate", '{"id": "P110"}'))["error"]
    assert "invalid arguments" in json.loads(kit.dispatch("get_rate", '{"product_id": '))["error"]
    assert json.loads(kit.dispatch("get_rate", '{"product_id": "BOOM"}')) == {"error": "tool failed: RuntimeError"}
