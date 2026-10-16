"""Tests for history.trim_history. Run with:  pytest -q test_history.py"""
from history import trim_history

SYS = {"role": "system", "content": "You are RR Finance Assist."}


def turns(n):
    out = []
    for i in range(n):
        out += [{"role": "user", "content": f"u{i}"}, {"role": "assistant", "content": f"a{i}"}]
    return out


def test_keeps_system_and_last_pairs():
    result = trim_history([SYS] + turns(5), max_turns=2)
    assert result[0] == SYS
    assert [m["content"] for m in result[1:]] == ["u3", "a3", "u4", "a4"]


def test_short_history_is_unchanged():
    messages = [SYS] + turns(1)
    assert trim_history(messages, max_turns=6) == messages


def test_never_starts_with_assistant():
    messages = [SYS] + turns(3) + [{"role": "user", "content": "new question"}]
    result = trim_history(messages, max_turns=2)
    assert result[1]["role"] == "user"
    assert result[-1]["content"] == "new question"


def test_works_without_system_message():
    assert trim_history(turns(3), max_turns=1) == turns(3)[-2:]


def test_does_not_modify_input():
    messages = [SYS] + turns(4)
    snapshot = list(messages)
    trim_history(messages, max_turns=1)
    assert messages == snapshot
