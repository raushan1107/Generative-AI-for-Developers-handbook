"""Drill 07.8: agent reliability, offline. A scripted fake model drives the real loop and the
real (stand-in) systems.  Run:  pytest -q test_agent.py"""
import json

import pytest

import desk
from agent import Agent
from desk_tools import WRITE_TOOLS, kit
from fake_llm import FakeLLM, calls, says

MEI = {"customer": "RR-10293"}
FREEZE = json.dumps({"card_last4": "4821"})
DISPUTE = json.dumps({"txn_id": "TX-1002", "reason": "charged_twice"})


@pytest.fixture(autouse=True)
def fresh_desk():
    desk.reset()


def agent(turns, approve=None, max_steps=8):
    return Agent(FakeLLM(turns), "fake", kit, "You are a test agent.", max_steps=max_steps,
                 write_tools=WRITE_TOOLS, approve=approve)


def test_read_then_answer():
    result = agent([calls("my_cards"), says("You have two cards.")]).run("Which cards do I have?", MEI)
    assert result.answer == "You have two cards." and result.stopped is None
    assert [s.tool for s in result.steps] == ["my_cards"] and result.llm_calls == 2


def test_write_needs_approval_and_runs_once_when_approved():
    asked = []
    result = agent([calls("freeze_card", FREEZE), says("Done.")],
                   approve=lambda name, args, ctx: asked.append(name) or (True, "")).run("Freeze my card", MEI)
    assert asked == ["freeze_card"] and result.steps[0].status == "ok"
    assert [a["action"] for a in desk.ACTIONS] == ["freeze_card"]


def test_rejected_write_changes_nothing_and_the_model_is_told():
    a = agent([calls("freeze_card", FREEZE), says("OK, I won't freeze it.")],
              approve=lambda name, args, ctx: (False, "customer said no"))
    result = a.run("Freeze my card", MEI)
    assert result.steps[0].status == "rejected" and desk.ACTIONS == []
    assert "did not approve" in a.client.requests[1]["messages"][-1]["content"]


def test_no_approver_means_writes_are_refused():
    result = agent([calls("freeze_card", FREEZE), says("I can't do that.")]).run("Freeze my card", MEI)
    assert result.steps[0].status == "rejected" and desk.ACTIONS == []


def test_tool_errors_are_observations_the_model_can_use():
    a = agent([calls("card_status", json.dumps({"card_last4": "9034"})), says("That isn't yours.")])
    result = a.run("Status of card 9034?", MEI)                        # Diego's card, not Mei's
    assert result.steps[0].status == "error"
    assert "not one of this customer's cards" in result.steps[0].result


def test_policy_lives_in_code_not_in_the_model():
    old = json.loads(kit.dispatch("dispute_quote", json.dumps({"txn_id": "TX-1006"}), MEI))
    assert old["allowed"] is False and "60 days" in old["reason"]       # 75 days old
    fresh = json.loads(kit.dispatch("dispute_quote", json.dumps({"txn_id": "TX-1002"}), MEI))
    assert fresh["allowed"] is True and fresh["amount_usd"] == 412.0


def test_step_budget_stops_a_runaway_agent():
    turns = [calls("recent_transactions", json.dumps({"card_last4": f"48{i:02d}"}), f"c{i}") for i in range(10)]
    result = agent(turns, max_steps=3).run("Find every payment", MEI)
    assert result.stopped == "max_steps" and result.llm_calls == 3


def test_repeating_the_same_call_is_detected_then_stopped():
    result = agent([calls("my_cards")] * 6).run("Loop forever", MEI)
    assert [s.status for s in result.steps] == ["ok", "ok", "repeated", "repeated"]
    assert result.stopped == "loop"


def test_idempotency_key_makes_a_retried_write_harmless():
    first = desk.open_dispute("RR-10293", "TX-1002", "charged_twice", key="k1")
    again = desk.open_dispute("RR-10293", "TX-1002", "charged_twice", key="k1")   # e.g. a retry after a timeout
    assert again["dispute_id"] == first["dispute_id"] and "already done" in again["note"]
    assert len(desk.ACTIONS) == 1


def test_a_second_dispute_for_the_same_payment_is_refused():
    desk.open_dispute("RR-10293", "TX-1002", "charged_twice")
    result = json.loads(kit.dispatch("open_dispute", DISPUTE, MEI))
    assert "already being disputed" in result["error"] and len(desk.ACTIONS) == 1


def test_flaky_services_raise_retryable_errors():
    desk.reset(flaky_rate=1.0)
    result = json.loads(kit.dispatch("my_cards", "{}", MEI))
    assert result["retryable"] is True and "timed out" in result["error"]
