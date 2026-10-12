"""Tests for validate_email. Run with:  pytest -q test_validate_email.py"""
import pytest

from validate_email import validate_email


@pytest.mark.parametrize("address", [
    "asha@traincrest.example",
    "  diego.r@mail.example.org ",
    "mei+courses@learn.example",
])
def test_valid(address):
    assert validate_email(address) == (True, "ok")


@pytest.mark.parametrize("address, reason", [
    ("", "empty"),
    ("no-at-sign.example", "must contain exactly one @"),
    ("two@@signs.example", "must contain exactly one @"),
    ("@traincrest.example", "missing name before @"),
    ("asha@localhost", "invalid domain"),
    ("asha@.example", "invalid domain"),
    ("asha@traincrest..example", "invalid domain"),
    ("asha kumar@traincrest.example", "contains spaces"),
    ("a" * 250 + "@x.example", "too long"),
])
def test_invalid(address, reason):
    assert validate_email(address) == (False, reason)
