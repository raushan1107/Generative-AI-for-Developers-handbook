"""Milestone 4: the streaming tool loop, driven by a scripted fake model. Run:  pytest -q"""
import json

from app import chat as chat_module
from app.chat import TOO_MANY_STEPS, ChatService
from tests.fakes import FakeClient, text, tool


def run(rounds, message="hi", customer="RR-10293"):
    fake = FakeClient(rounds)
    events = list(ChatService(client=fake).stream("session-1234", message, customer_id=customer))
    return events, fake.chat.completions.calls


def test_plain_answer_needs_one_call():
    events, calls = run([text("Hello Mei!")])
    assert len(calls) == 1 and events[-1]["type"] == "done" and events[-1]["tools"] == []


def test_tool_call_then_answer():
    events, calls = run([tool("quote_fee_refund", '{"account_id": "AC-5512"}'),
                         text("We'll refund $87: two fees charged in error and one courtesy refund.")])
    kinds = [e["type"] for e in events]
    assert "tool" in kinds and kinds[-1] == "done"
    assert events[-1]["tools"] == ["quote_fee_refund"]
    assert events[-1]["tokens_in"] == 200                      # usage added across both calls
    # Second call carried the assistant tool request and the tool result, linked by id.
    sent = calls[1]["messages"]
    assert sent[-2]["tool_calls"][0]["function"]["arguments"] == '{"account_id": "AC-5512"}'
    result = json.loads(sent[-1]["content"])
    assert sent[-1]["tool_call_id"] == "call_1" and result["refund_usd"] == 87


def test_tools_are_sent_strict_and_one_at_a_time():
    _, calls = run([text("ok")])
    assert calls[0]["parallel_tool_calls"] is False
    assert all(t["function"]["strict"] for t in calls[0]["tools"])


def test_identity_is_enforced_even_if_the_model_asks():
    events, calls = run([tool("get_card_status", '{"card_last4": "9034"}'), text("Sorry, I can't see that.")])
    assert "not allowed" in calls[1]["messages"][-1]["content"]
    assert events[-1]["tools"] == ["get_card_status:error"]


def test_loop_stops_after_max_rounds(monkeypatch):
    monkeypatch.setattr(chat_module, "MAX_TOOL_ROUNDS", 2)
    events, calls = run([tool("list_my_accounts", "{}")] * 3)
    assert len(calls) == 3
    assert {"type": "replace", "text": TOO_MANY_STEPS} in events


def test_errors_are_friendly_and_history_is_clean():
    fake = FakeClient([{"raise": "rate"}])
    service = ChatService(client=fake)
    events = list(service.stream("session-1234", "hi", customer_id=None))
    assert events[-1]["type"] == "error" and "busy" in events[-1]["message"]
    assert service.sessions["session-1234"] == []
