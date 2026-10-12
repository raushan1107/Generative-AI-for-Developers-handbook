"""Tests for robust.py, using the chaos scenarios. Run:  pytest -q test_robust.py"""
import pytest

from lab04_10_chaos import SCENARIOS, FakeModel, Reply
from robust import extract_json, structured_call

EXPECTED = {
    "clean JSON": ("ok", 1), "fenced JSON": ("ok", 1), "sentence + JSON": ("ok", 1),
    "wrong value, then fixed": ("ok", 2), "garbage twice": ("invalid", 2),
    "cut off, then fixed": ("ok", 2), "cut off twice": ("truncated", 2),
    "refusal": ("refused", 1), "content filter": ("blocked", 1),
}


@pytest.mark.parametrize("name", list(SCENARIOS))
def test_each_failure_mode_has_a_clear_outcome(name):
    out = structured_call(FakeModel(*SCENARIOS[name]), "fake", [{"role": "user", "content": "x"}], Reply)
    assert (out.status, out.attempts) == EXPECTED[name]
    assert (out.value is not None) == (out.status == "ok")


def test_extract_json():
    assert extract_json('```json\n{"a": 1}\n```') == '{"a": 1}'
    assert extract_json('Here: {"a": {"b": 2}} done') == '{"a": {"b": 2}}'
