"""Milestone 7: proposals, approval, execution, and agent reliability guards. Offline. Run:  pytest -q"""
import copy
import json

import pytest

from app import actions, backend
from app.chat import GARBLED, ChatService
from app.tools import kit
from tests.fakes import FakeClient, text, tool

MEI, DIEGO, ASHA = {"learner_id": "L-MEI"}, {"learner_id": "L-DIEGO"}, {"learner_id": "L-ASHA"}


@pytest.fixture(autouse=True)
def fresh_backend(monkeypatch, tmp_path):
    monkeypatch.setattr(backend, "LABS", copy.deepcopy(backend.LABS))
    monkeypatch.setattr(backend, "ENROLMENTS", copy.deepcopy(backend.ENROLMENTS))
    monkeypatch.setattr(backend, "_DONE", {})
    monkeypatch.setattr(backend, "ACTIONS_FILE", tmp_path / "actions.jsonl")


def call(name, args, context):
    context = {**context, "proposals": []}
    return json.loads(kit.dispatch(name, json.dumps(args), context)), context["proposals"]


def test_request_tools_propose_but_change_nothing():
    before = dict(backend.LABS["TC-10293"])
    result, proposals = call("request_lab_extension", {"enrolment_id": "TC-10293"}, MEI)
    assert result["status"] == "awaiting_learner_approval" and result["action_id"].startswith("A-")
    assert proposals[0]["summary"] == "Extend the lab for TC-10293 by 7 days, free (one-time)."
    assert backend.LABS["TC-10293"] == before and not backend.ACTIONS_FILE.exists()


def test_request_tools_check_rules_and_identity_first():
    assert "no free extension" in call("request_lab_extension", {"enrolment_id": "TC-31002"}, ASHA)[0]["error"]
    assert "not allowed" in call("request_lab_extension", {"enrolment_id": "TC-31002"}, MEI)[0]["error"]
    bad, _ = call("request_reschedule", {"enrolment_id": "TC-20877", "new_start_date": "2030-01-01"}, DIEGO)
    assert "isn't an available date" in bad["error"]


def test_reschedule_proposal_carries_the_fee_from_policy():
    new = backend.upcoming_sessions("C110")[1]
    result, proposals = call("request_reschedule", {"enrolment_id": "TC-20877", "new_start_date": new}, DIEGO)
    assert proposals[0]["fee_usd"] == 50 and "$50 fee" in result["summary"]        # starts in 5 days


def test_approve_executes_once_and_logs():
    store = actions.ActionStore()
    _, proposals = call("request_lab_extension", {"enrolment_id": "TC-10293"}, MEI)
    store.add("s1", proposals[0])
    first = store.decide("s1", proposals[0]["action_id"], "L-MEI", approve=True)
    assert first["status"] == "done" and backend.LABS["TC-10293"]["free_extension_used"]
    assert store.decide("s1", proposals[0]["action_id"], "L-MEI", approve=True)["status"] == "unknown"   # once only
    assert len(backend.ACTIONS_FILE.read_text().splitlines()) == 1


def test_decline_wrong_learner_and_expiry_change_nothing(monkeypatch):
    store = actions.ActionStore()
    for _ in range(3):
        _, proposals = call("request_lab_extension", {"enrolment_id": "TC-10293"}, MEI)
        store.add("s1", proposals[0])
    a, b, c = list(store.pending)
    assert store.decide("s1", a, "L-MEI", approve=False)["status"] == "declined"
    assert store.decide("s1", b, "L-DIEGO", approve=True)["status"] == "unknown"     # not Diego's to approve
    store.pending[c]["created"] -= actions.EXPIRY_S + 1
    assert store.decide("s1", c, "L-MEI", approve=True)["status"] == "expired"
    assert backend.LABS["TC-10293"]["free_extension_used"] is False


def test_backend_writes_are_idempotent():
    first = backend.extend_lab("TC-10293", key="A-1")
    assert backend.extend_lab("TC-10293", key="A-1") == first                      # a retry: same result, no error
    with pytest.raises(backend.ActionError):
        backend.extend_lab("TC-10293", key="A-2")                                  # a second, different request


def test_chat_returns_approvals_and_records_the_decision():
    fake = FakeClient([tool("request_lab_extension", '{"enrolment_id": "TC-10293"}'),
                       text("I've prepared a free 7-day extension. Please approve it below.")])
    service = ChatService(client=fake)
    done = list(service.stream("session-1234", "extend my lab please", learner_id="L-MEI"))[-1]
    (approval,) = done["approvals"]
    assert approval["summary"].startswith("Extend the lab for TC-10293")
    result = service.decide("session-1234", approval["action_id"], "L-MEI", approve=True)
    assert result["status"] == "done" and "is now open until" in result["message"]
    assert service.sessions["session-1234"][-1]["content"].startswith(f"[{approval['action_id']} done]")


def test_repeated_identical_tool_calls_are_refused():
    fake = FakeClient([tool("list_my_enrolments", "{}", f"c{i}") for i in range(3)] + [text("Done.")])
    list(ChatService(client=fake).stream("session-1234", "loop", learner_id="L-MEI"))
    third = [m for m in fake.chat.completions.calls[-1]["messages"] if m["role"] == "tool"][2]
    assert "already made this exact call" in third["content"]


def test_a_tool_call_written_as_text_is_never_shown():
    fake = FakeClient([text('{"name": "quote_extLAB", "parameters": {"enrolment_id": "TC-12345"}}')])
    events = list(ChatService(client=fake).stream("session-1234", "how much?", learner_id=None))
    assert {"type": "replace", "text": GARBLED} in events


def test_session_context_has_only_the_signed_in_learners_enrolments():
    fake = FakeClient([text("Hi Mei."), text("Hello.")])
    service = ChatService(client=fake)
    list(service.stream("session-1234", "hi", learner_id="L-MEI"))
    system = fake.chat.completions.calls[0]["messages"][0]["content"]
    assert "TC-10293" in system and "TC-10477" in system and "TC-20877" not in system   # not Diego's
    list(service.stream("session-5678", "hi", learner_id=None))
    assert "Signed-in learner" not in fake.chat.completions.calls[1]["messages"][0]["content"]
