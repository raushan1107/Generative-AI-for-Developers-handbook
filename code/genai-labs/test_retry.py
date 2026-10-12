"""Tests for retry.retry. They never call a real API and run in milliseconds.
Run with:  pytest -q test_retry.py"""
import pytest

from retry import retry


class Flaky(Exception):
    pass


def test_succeeds_after_transient_failures():
    calls, waits = [], []

    @retry(Flaky, max_attempts=4, base=1, sleep=waits.append)
    def sometimes():
        calls.append(1)
        if len(calls) < 3:
            raise Flaky()
        return "ok"

    assert sometimes() == "ok"
    assert len(calls) == 3
    assert len(waits) == 2
    assert 1 <= waits[0] <= 1.25 and 2 <= waits[1] <= 2.5   # exponential, plus jitter


def test_gives_up_after_max_attempts():
    calls = []

    @retry(Flaky, max_attempts=3, sleep=lambda s: None)
    def always_fails():
        calls.append(1)
        raise Flaky()

    with pytest.raises(Flaky):
        always_fails()
    assert len(calls) == 3


def test_does_not_retry_other_errors():
    calls = []

    @retry(Flaky, sleep=lambda s: None)
    def wrong_input():
        calls.append(1)
        raise ValueError("bad request")

    with pytest.raises(ValueError):
        wrong_input()
    assert len(calls) == 1


def test_wait_is_capped():
    waits = []

    @retry(Flaky, max_attempts=8, base=10, cap=30, sleep=waits.append)
    def always_fails():
        raise Flaky()

    with pytest.raises(Flaky):
        always_fails()
    assert max(waits) <= 30 * 1.25
