"""Drill 07.8: agent reliability, offline. A scripted fake model drives the real loop and the
real (stand-in) systems.  Run:  pytest -q test_agent.py"""
import json

import pytest

import desk
from agent import Agent
from desk_tools import WRITE_TOOLS, kit
from fake_llm import FakeLLM, calls, says

MEI = {"learner": "L-MEI"}
EXTEND = json.dumps({"enrolment_id": "TC-10293"})


@pytest.fixture(autouse=True)
def fresh_desk():
    desk.reset()


def agent(turns, approve=None, max_steps=8):
    return Agent(FakeLLM(turns), "fake", kit, "You are a test agent.", max_steps=max_steps,
                 write_tools=WRITE_TOOLS, approve=approve)


def test_read_then_answer():
    result = agent([calls("my_enrolments"), says("You have two enrolments.")]).run("What am I enrolled in?", MEI)
    assert result.answer == "You have two enrolments." and result.stopped is None
    assert [s.tool for s in result.steps] == ["my_enrolments"] and result.llm_calls == 2


def test_write_needs_approval_and_runs_once_when_approved():
    asked = []
    result = agent([calls("extend_lab", EXTEND), says("Done.")],
                   approve=lambda name, args, ctx: asked.append(name) or (True, "")).run("Extend my lab", MEI)
    assert asked == ["extend_lab"] and result.steps[0].status == "ok"
    assert [a["action"] for a in desk.ACTIONS] == ["extend_lab"]


def test_rejected_write_changes_nothing_and_the_model_is_told():
    a = agent([calls("extend_lab", EXTEND), says("OK, I won't extend it.")],
              approve=lambda name, args, ctx: (False, "learner said no"))
    result = a.run("Extend my lab", MEI)
    assert result.steps[0].status == "rejected" and desk.ACTIONS == []
    assert "did not approve" in a.client.requests[1]["messages"][-1]["content"]


def test_no_approver_means_writes_are_refused():
    result = agent([calls("extend_lab", EXTEND), says("I can't do that.")]).run("Extend my lab", MEI)
    assert result.steps[0].status == "rejected" and desk.ACTIONS == []


def test_tool_errors_are_observations_the_model_can_use():
    a = agent([calls("lab_status", json.dumps({"enrolment_id": "TC-20877"})), says("That isn't yours.")])
    result = a.run("Lab status of TC-20877?", MEI)                      # Diego's enrolment, not Mei's
    assert result.steps[0].status == "error"
    assert "not one of this learner's enrolments" in result.steps[0].result


def test_step_budget_stops_a_runaway_agent():
    turns = [calls("upcoming_sessions", json.dumps({"course_id": f"C1{i:02d}"}), f"c{i}") for i in range(10)]
    result = agent(turns, max_steps=3).run("Find every session", MEI)
    assert result.stopped == "max_steps" and result.llm_calls == 3


def test_repeating_the_same_call_is_detected_then_stopped():
    result = agent([calls("my_enrolments")] * 6).run("Loop forever", MEI)
    assert [s.status for s in result.steps] == ["ok", "ok", "repeated", "repeated"]
    assert result.stopped == "loop"


def test_idempotency_key_makes_a_retried_write_harmless():
    first = desk.extend_lab("L-MEI", "TC-10293", key="k1")
    again = desk.extend_lab("L-MEI", "TC-10293", key="k1")             # e.g. a retry after a timeout
    assert again["lab_until"] == first["lab_until"] and "already done" in again["note"]
    assert len(desk.ACTIONS) == 1


def test_flaky_services_raise_retryable_errors():
    desk.reset(flaky_rate=1.0)
    result = json.loads(kit.dispatch("my_enrolments", "{}", MEI))
    assert result["retryable"] is True and "timed out" in result["error"]
