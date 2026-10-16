"""Tests for validate_email. Run with:  pytest -q test_validate_email.py"""
import pytest

from validate_email import validate_email


@pytest.mark.parametrize("address", [
    "asha@rrfinance.example",
    "  diego.r@mail.example.org ",
    "mei+savings@bank.example",
])
def test_valid(address):
    assert validate_email(address) == (True, "ok")


@pytest.mark.parametrize("address, reason", [
    ("", "empty"),
    ("no-at-sign.example", "must contain exactly one @"),
    ("two@@signs.example", "must contain exactly one @"),
    ("@rrfinance.example", "missing name before @"),
    ("asha@localhost", "invalid domain"),
    ("asha@.example", "invalid domain"),
    ("asha@rrfinance..example", "invalid domain"),
    ("asha nair@rrfinance.example", "contains spaces"),
    ("a" * 250 + "@x.example", "too long"),
])
def test_invalid(address, reason):
    assert validate_email(address) == (False, reason)
