"""Tests for validators.py. Run:  pytest -q test_validators.py"""
from datetime import date

import pytest
from pydantic import ValidationError

import validators
from validators import CaseDraft, unsupported_amounts

GOOD = {"category": "dispute", "summary": "Customer was charged twice for the same $412 flight.",
        "customer_id": "RR-10293", "urgency": "medium", "transaction_date": "2026-09-09"}


@pytest.fixture(autouse=True)
def fixed_today(monkeypatch):
    monkeypatch.setattr(validators, "today", lambda: date(2026, 10, 11))


def test_good_case_passes():
    assert CaseDraft.model_validate(GOOD).transaction_date == "2026-09-09"


@pytest.mark.parametrize("change, message", [
    ({"customer_id": "10293"}, "RR-12345"),
    ({"summary": "help"}, "10 to 200"),
    ({"transaction_date": "09/09/2026"}, "YYYY-MM-DD"),
    ({"transaction_date": "2026-10-20"}, "future"),
    ({"transaction_date": "2026-06-01"}, "90 days"),
    ({"customer_id": None}, "needs the customer_id"),
])
def test_business_rules(change, message):
    with pytest.raises(ValidationError) as info:
        CaseDraft.model_validate({**GOOD, **change})
    assert message in str(info.value)


def test_other_categories_may_omit_the_customer():
    assert CaseDraft.model_validate({**GOOD, "category": "other", "customer_id": None}).customer_id is None


def test_facts_layer_catches_invented_amounts():
    answer = "We'll refund one $29 overdraft fee, and express delivery of the new card costs $15."
    assert unsupported_amounts(answer, {29.0, 15.0}) == []
    assert unsupported_amounts("Good news: we'll refund all $145 of fees!", {29.0}) == [145.0]
