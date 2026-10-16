"""Milestone 7: proposals, approval, execution, and agent reliability guards. Offline. Run:  pytest -q"""
import copy
import json

import pytest

from app import actions, backend
from app.chat import GARBLED, ChatService
from app.tools import kit
from tests.fakes import FakeClient, text, tool

MEI, DIEGO, ASHA = {"customer_id": "RR-10293"}, {"customer_id": "RR-20877"}, {"customer_id": "RR-31002"}


@pytest.fixture(autouse=True)
def fresh_backend(monkeypatch, tmp_path):
    monkeypatch.setattr(backend, "CARDS", copy.deepcopy(backend.CARDS))
    monkeypatch.setattr(backend, "DISPUTES", {})
    monkeypatch.setattr(backend, "_DONE", {})
    monkeypatch.setattr(backend, "ACTIONS_FILE", tmp_path / "actions.jsonl")


def call(name, args, context):
    context = {**context, "proposals": []}
    return json.loads(kit.dispatch(name, json.dumps(args), context)), context["proposals"]


def test_request_tools_propose_but_change_nothing():
    before = dict(backend.CARDS["4821"])
    result, proposals = call("request_card_freeze", {"card_last4": "4821"}, MEI)
    assert result["status"] == "awaiting_customer_approval" and result["action_id"].startswith("A-")
    assert proposals[0]["summary"].startswith("Freeze your Cashback Card ending 4821.")
    assert backend.CARDS["4821"] == before and not backend.ACTIONS_FILE.exists()


def test_request_tools_check_rules_and_identity_first():
    assert "already frozen" in call("request_card_freeze", {"card_last4": "5560"}, ASHA)[0]["error"]
    assert "not allowed" in call("request_card_freeze", {"card_last4": "5560"}, MEI)[0]["error"]
    old, _ = call("request_dispute", {"txn_id": "TX-1006", "reason": "wrong_amount"}, MEI)      # 75 days ago
    assert "can't be disputed" in old["error"]


def test_dispute_proposal_carries_the_amount_and_date_from_code():
    result, proposals = call("request_dispute", {"txn_id": "TX-1002", "reason": "charged_twice"}, MEI)
    assert "$412.00 to SkyHigh Airlines" in result["summary"] and "provisional credit by" in result["summary"]
    assert proposals[0]["args"] == {"txn_id": "TX-1002", "reason": "charged_twice"}


def test_approve_executes_once_and_logs():
    store = actions.ActionStore()
    _, proposals = call("request_card_freeze", {"card_last4": "4821"}, MEI)
    store.add("s1", proposals[0])
    first = store.decide("s1", proposals[0]["action_id"], "RR-10293", approve=True)
    assert first["status"] == "done" and backend.CARDS["4821"]["status"] == "frozen"
    assert store.decide("s1", proposals[0]["action_id"], "RR-10293", approve=True)["status"] == "unknown"   # once only
    assert len(backend.ACTIONS_FILE.read_text().splitlines()) == 1


def test_decline_wrong_customer_and_expiry_change_nothing():
    store = actions.ActionStore()
    for _ in range(3):
        _, proposals = call("request_card_freeze", {"card_last4": "4821"}, MEI)
        store.add("s1", proposals[0])
    a, b, c = list(store.pending)
    assert store.decide("s1", a, "RR-10293", approve=False)["status"] == "declined"
    assert store.decide("s1", b, "RR-20877", approve=True)["status"] == "unknown"     # not Diego's to approve
    store.pending[c]["created"] -= actions.EXPIRY_S + 1
    assert store.decide("s1", c, "RR-10293", approve=True)["status"] == "expired"
    assert backend.CARDS["4821"]["status"] == "active"


def test_backend_writes_are_idempotent():
    first = backend.open_dispute("TX-1002", "charged_twice", "2026-10-25", key="A-000001")
    assert backend.open_dispute("TX-1002", "charged_twice", "2026-10-25", key="A-000001") == first   # a retry
    with pytest.raises(backend.ActionError):
        backend.open_dispute("TX-1002", "charged_twice", "2026-10-25", key="A-000002")   # a second dispute: refused


def test_chat_returns_approvals_and_records_the_decision():
    fake = FakeClient([tool("request_dispute", '{"txn_id": "TX-1002", "reason": "charged_twice"}'),
                       text("I've prepared a dispute for the duplicate charge. Please approve it below.")])
    service = ChatService(client=fake)
    done = list(service.stream("session-1234", "I was charged twice", customer_id="RR-10293"))[-1]
    (approval,) = done["approvals"]
    assert approval["summary"].startswith("Dispute $412.00 to SkyHigh Airlines")
    result = service.decide("session-1234", approval["action_id"], "RR-10293", approve=True)
    assert result["status"] == "done" and "provisional credit" in result["message"]
    assert service.sessions["session-1234"][-1]["content"].startswith(f"[{approval['action_id']} done]")


def test_repeated_identical_tool_calls_are_refused():
    fake = FakeClient([tool("list_my_accounts", "{}", f"c{i}") for i in range(3)] + [text("Done.")])
    list(ChatService(client=fake).stream("session-1234", "loop", customer_id="RR-10293"))
    third = [m for m in fake.chat.completions.calls[-1]["messages"] if m["role"] == "tool"][2]
    assert "already made this exact call" in third["content"]


def test_a_tool_call_written_as_text_is_never_shown():
    fake = FakeClient([text('{"name": "quote_feeREF", "parameters": {"account_id": "AC-1234"}}')])
    events = list(ChatService(client=fake).stream("session-1234", "how much?", customer_id=None))
    assert {"type": "replace", "text": GARBLED} in events


def test_session_context_has_only_the_signed_in_customers_accounts():
    fake = FakeClient([text("Hi Mei."), text("Hello.")])
    service = ChatService(client=fake)
    list(service.stream("session-1234", "hi", customer_id="RR-10293"))
    system = fake.chat.completions.calls[0]["messages"][0]["content"]
    assert "AC-5512" in system and "4821" in system and "9034" not in system           # not Diego's card
    list(service.stream("session-5678", "hi", customer_id=None))
    assert "Signed-in customer" not in fake.chat.completions.calls[1]["messages"][0]["content"]
