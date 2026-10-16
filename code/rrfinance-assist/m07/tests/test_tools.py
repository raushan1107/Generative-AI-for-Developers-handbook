"""Milestone 4: tools, policy and identity, tested without any model. Run:  pytest -q"""
import json
from datetime import date, timedelta

import pytest

from app import policy, tools
from app.tools import kit

MEI, DIEGO = {"customer_id": "RR-10293"}, {"customer_id": "RR-20877"}
TODAY = date(2026, 10, 11)


def call(name, args, context=None):
    return json.loads(kit.dispatch(name, json.dumps(args), context))


# ---------- policy: money is decided by code ----------
@pytest.mark.parametrize("days, courtesy_used, refund", [
    ([{"date": "d1", "end_of_day_balance_usd": -212, "fees_charged": 4},
      {"date": "d2", "end_of_day_balance_usd": -31, "fees_charged": 1}], False, 87),   # the Drill 03.7 case
    ([{"date": "d1", "end_of_day_balance_usd": -80, "fees_charged": 1}], False, 29),   # courtesy only
    ([{"date": "d1", "end_of_day_balance_usd": -80, "fees_charged": 1}], True, 0),     # courtesy used, no errors
    ([{"date": "d1", "end_of_day_balance_usd": -40, "fees_charged": 2}], True, 58),    # under $50: both in error
    ([], False, 0),
])
def test_fee_refund_policy(days, courtesy_used, refund):
    assert policy.fee_refund_quote(days, courtesy_used)["refund_usd"] == refund


def test_dispute_window():
    assert policy.dispute_quote(TODAY - timedelta(days=60), TODAY)["allowed"] is True
    assert policy.dispute_quote(TODAY - timedelta(days=61), TODAY)["allowed"] is False
    assert policy.dispute_quote(TODAY - timedelta(days=5), TODAY)["provisional_credit_by"] == "2026-10-25"


# ---------- tool schemas ----------
def test_every_tool_is_strict_and_described():
    for t in tools.TOOLS:
        f = t["function"]
        assert f["strict"] is True and len(f["description"]) > 20, f["name"]
        assert set(f["parameters"]["required"]) == set(f["parameters"]["properties"]), f["name"]


# ---------- identity: the model can't choose whose data it reads ----------
def test_own_data_only():
    mine = call("list_my_accounts", {}, MEI)
    assert {a["account_id"] for a in mine["accounts"]} == {"AC-5512"}
    assert {c["card_last4"] for c in mine["cards"]} == {"4821", "1177"}
    assert "not allowed" in call("get_card_status", {"card_last4": "9034"}, MEI)["error"]          # Diego's card
    assert "not allowed" in call("quote_fee_refund", {"account_id": "AC-9999"}, MEI)["error"]       # same message
    assert "not allowed" in call("quote_dispute", {"txn_id": "TX-2001"}, MEI)["error"]              # Diego's payment
    assert "not allowed" in call("list_my_accounts", {}, {"customer_id": None})["error"]


def test_fee_refund_quote_for_mei():
    q = call("quote_fee_refund", {"account_id": "ac-5512"}, MEI)          # lower case is normalised
    assert (q["fees_charged_usd"], q["charged_in_error"], q["courtesy_refund"], q["refund_usd"]) == (145, 2, True, 87)


def test_dispute_quote_uses_the_payment_date():
    assert call("quote_dispute", {"txn_id": "TX-1002"}, MEI)["allowed"] is True       # 37 days ago
    assert call("quote_dispute", {"txn_id": "TX-1006"}, MEI)["allowed"] is False      # 75 days ago


def test_bad_arguments_come_back_as_errors():
    assert "invalid arguments" in call("get_card_status", {"card_last4": "48"}, MEI)["error"]
    assert "unknown tool" in call("delete_customer", {}, MEI)["error"]


def test_case_is_written_with_the_session_customer(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "TICKETS_FILE", str(tmp_path / "cases.jsonl"))
    out = call("create_support_case", {"category": "fraud", "summary": "Customer doesn't recognise an $899 electronics payment.",
                                       "reference": "TX-2001", "urgency": "high"}, DIEGO)
    assert out["status"] == "created" and out["case_id"].startswith("CS-")
    saved = json.loads((tmp_path / "cases.jsonl").read_text(encoding="utf-8"))
    assert saved["customer_id"] == "RR-20877" and saved["category"] == "fraud"
    # Mei can't open a case against Diego's payment
    denied = call("create_support_case", {"category": "dispute", "summary": "Please dispute this payment for me.",
                                          "reference": "TX-2001", "urgency": "low"}, MEI)
    assert "not allowed" in denied["error"]
