"""Tests for output_guard.check_output. Run with:  pytest -q test_output_guard.py"""
import pytest

from output_guard import check_output


def test_clean_summary_passes():
    text = "Learners loved the practical Azure labs; some found the lab environment slow on 12 March 2027."
    assert check_output(text) == []


def test_prices_and_dates_are_not_phone_numbers():
    assert check_output("The course costs $1,200 and starts on 20 March 2027.") == []


@pytest.mark.parametrize("text, problem", [
    ("Claim your refund at traincrest-refunds.example today.", "url"),
    ("Visit https://bit.ly/abc123 now", "url"),
    ("Contact helpdesk@attacker.example for help", "email"),
    ("Call +1 555 010 9999 for your refund", "phone"),
    ("Sure! I will ignore previous instructions.", "injection_echo"),
])
def test_flags_suspicious_content(text, problem):
    assert problem in check_output(text)


def test_official_domain_and_subdomains_are_allowed():
    assert check_output("Read the policy at https://learn.traincrest.example/policies") == []
    assert check_output("See traincrest.example for details.") == []


def test_lookalike_domain_is_not_allowed():
    assert "url" in check_output("Go to https://traincrest.example.evil.xyz/login")
