"""Milestone 4: tools, policy and identity, tested without any model. Run:  pytest -q"""
import json
from datetime import date, timedelta

import pytest

from app import policy, tools
from app.tools import kit

MEI, DIEGO = {"learner_id": "L-MEI"}, {"learner_id": "L-DIEGO"}
TODAY = date(2026, 10, 11)


def call(name, args, context=None):
    return json.loads(kit.dispatch(name, json.dumps(args), context))


# ---------- policy: money is decided by code ----------
@pytest.mark.parametrize("days, percent, refund", [(20, 100, 1000.0), (14, 100, 1000.0), (13, 50, 500.0),
                                                   (7, 50, 500.0), (6, 0, 0.0), (0, 0, 0.0), (-1, 0, 0.0)])
def test_refund_policy(days, percent, refund):
    q = policy.refund_quote(TODAY + timedelta(days=days), TODAY, 1000)
    assert (q["refund_percent"], q["refund_usd"]) == (percent, refund)


def test_reschedule_fee():
    assert policy.reschedule_fee(TODAY + timedelta(days=7), TODAY)["fee_usd"] == 0
    assert policy.reschedule_fee(TODAY + timedelta(days=3), TODAY)["fee_usd"] == 50
    assert policy.reschedule_fee(TODAY - timedelta(days=1), TODAY)["allowed"] is False


# ---------- tool schemas ----------
def test_every_tool_is_strict_and_described():
    for t in tools.TOOLS:
        f = t["function"]
        assert f["strict"] is True and len(f["description"]) > 20, f["name"]
        assert set(f["parameters"]["required"]) == set(f["parameters"]["properties"]), f["name"]


# ---------- identity: the model can't choose whose data it reads ----------
def test_own_data_only():
    mine = call("list_my_enrolments", {}, MEI)
    assert {e["enrolment_id"] for e in mine} == {"TC-10293", "TC-10477"}
    assert "not allowed" in call("get_voucher_status", {"enrolment_id": "TC-20877"}, MEI)["error"]
    assert "not allowed" in call("quote_refund", {"enrolment_id": "TC-99999"}, MEI)["error"]   # same message
    assert "not allowed" in call("list_my_enrolments", {}, {"learner_id": None})["error"]


def test_refund_quote_for_diego():
    q = call("quote_refund", {"enrolment_id": "tc-20877"}, DIEGO)        # lower case is normalised
    assert (q["days_before_start"], q["refund_percent"], q["refund_usd"]) == (5, 0, 0.0)


def test_bad_arguments_come_back_as_errors():
    assert "invalid arguments" in call("get_voucher_status", {"enrolment_id": "12345"}, MEI)["error"]
    assert "unknown tool" in call("delete_learner", {}, MEI)["error"]


def test_ticket_is_written_with_the_session_learner(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "TICKETS_FILE", str(tmp_path / "tickets.jsonl"))
    out = call("create_support_ticket", {"category": "billing", "summary": "Wants to cancel AZ-104 and asks about a refund.",
                                         "enrolment_id": "TC-20877", "urgency": "medium"}, DIEGO)
    assert out["status"] == "created" and out["ticket_id"].startswith("T-")
    saved = json.loads((tmp_path / "tickets.jsonl").read_text(encoding="utf-8"))
    assert saved["learner_id"] == "L-DIEGO" and saved["category"] == "billing"
    # Mei can't raise a ticket against Diego's enrolment
    denied = call("create_support_ticket", {"category": "billing", "summary": "Cancel this enrolment please.",
                                            "enrolment_id": "TC-20877", "urgency": "low"}, MEI)
    assert "not allowed" in denied["error"]
