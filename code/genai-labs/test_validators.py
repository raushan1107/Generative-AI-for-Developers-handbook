"""Tests for validators.py. Run:  pytest -q test_validators.py"""
from datetime import date

import pytest
from pydantic import ValidationError

import validators
from validators import TicketDraft, unsupported_amounts

GOOD = {"category": "scheduling", "summary": "Learner wants to move AZ-104 to a later date.",
        "enrolment_id": "TC-20877", "urgency": "medium", "preferred_date": "2026-11-16"}


@pytest.fixture(autouse=True)
def fixed_today(monkeypatch):
    monkeypatch.setattr(validators, "today", lambda: date(2026, 10, 11))


def test_good_ticket_passes():
    assert TicketDraft.model_validate(GOOD).preferred_date == "2026-11-16"


@pytest.mark.parametrize("change, message", [
    ({"enrolment_id": "20877"}, "TC-12345"),
    ({"summary": "help"}, "10 to 200"),
    ({"preferred_date": "16/11/2026"}, "YYYY-MM-DD"),
    ({"preferred_date": "2026-10-01"}, "future"),
    ({"preferred_date": "2028-01-01"}, "365 days"),
    ({"enrolment_id": None}, "needs the enrolment_id"),
])
def test_business_rules(change, message):
    with pytest.raises(ValidationError) as info:
        TicketDraft.model_validate({**GOOD, **change})
    assert message in str(info.value)


def test_facts_layer_catches_invented_amounts():
    answer = "You'll get a 50% refund of $745.00, and a $50 fee applies if you reschedule."
    assert unsupported_amounts(answer, {745.0, 50.0}) == []
    assert unsupported_amounts("Good news: a full refund of $1,490!", {745.0}) == [1490.0]
