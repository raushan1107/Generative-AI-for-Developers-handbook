import pytest

from app.architecture import SessionStore, new_trace_id, select_deployment
from app.chat import ChatService
from tests.fakes import FakeClient


def test_routes_only_configured_tasks():
    assert select_deployment("triage", {"triage": "chat-small"}) == "chat-small"
    with pytest.raises(ValueError, match="Unconfigured task"):
        select_deployment("customer supplied name", {"triage": "chat-small"})


def test_empty_deployment_is_rejected():
    with pytest.raises(ValueError, match="Empty deployment"):
        select_deployment("draft", {"draft": " "})


def test_trace_ids_are_unique_and_safe_for_logs():
    first, second = new_trace_id(), new_trace_id()
    assert first != second
    assert len(first) == 32 and all(char in "0123456789abcdef" for char in first)


def test_session_round_trips_and_updates(tmp_path):
    store = SessionStore(tmp_path / "sessions.sqlite")
    store.save("s-1", [{"role": "user", "content": "Help with a dispute"}], 500)
    assert store.load("s-1", now=100) == [
        {"role": "user", "content": "Help with a dispute"}
    ]
    store.save("s-1", [{"role": "assistant", "content": "I can help"}], 600)
    assert store.load("s-1", now=100) == [
        {"role": "assistant", "content": "I can help"}
    ]


def test_expired_session_is_deleted(tmp_path):
    store = SessionStore(tmp_path / "sessions.sqlite")
    store.save("s-expired", [], expires_at=100)
    assert store.load("s-expired", now=100) is None
    assert store.load("s-expired", now=50) is None


def test_invalid_session_is_rejected(tmp_path):
    store = SessionStore(tmp_path / "sessions.sqlite")
    with pytest.raises(ValueError, match="session ID"):
        store.save("", [], expires_at=100)


def test_chat_service_persists_completed_turns(tmp_path):
    store = SessionStore(tmp_path / "sessions.sqlite")
    service = ChatService(
        client=FakeClient(rounds=[{"text": "I can help with the dispute."}]),
        session_store=store,
    )
    list(service.stream("session-1234", "I recognize a duplicate charge."))
    assert store.load("session-1234") == [
        {"role": "user", "content": "I recognize a duplicate charge."},
        {"role": "assistant", "content": "I can help with the dispute. "},
    ]


def test_reset_deletes_persisted_history(tmp_path):
    store = SessionStore(tmp_path / "sessions.sqlite")
    store.save("session-1234", [{"role": "user", "content": "question"}], 9999999999)
    service = ChatService(client=FakeClient(), session_store=store)
    service.reset("session-1234")
    assert store.load("session-1234") is None
