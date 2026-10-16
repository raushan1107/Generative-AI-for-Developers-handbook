"""Tests for schema_lint.py and the business enquiry schema. Run:  pytest -q test_schema_lint.py"""
from typing import Optional

import pytest
from pydantic import BaseModel, Field, ValidationError

from business_enquiry import BusinessEnquiry
from schema_lint import lint, strict_schema


class TooClever(BaseModel):
    customer_id: str = Field(pattern=r"^RR-\d{5}$")        # pattern: not supported
    summary: str = Field(max_length=200)                    # maxLength: not supported
    cards: int = Field(ge=1, le=500)                        # minimum/maximum: not supported


class Level5(BaseModel):
    x: int


class Level4(BaseModel):
    d: Level5


class Level3(BaseModel):
    c: Level4


class Level2(BaseModel):
    b: Level3


class Level1(BaseModel):
    a: Level2


class TooDeep(BaseModel):
    root: Level1
    note: Optional[str]


def test_reference_schema_is_clean():
    assert lint(strict_schema(BusinessEnquiry)) == []


def test_unsupported_keywords_are_reported():
    problems = " ".join(lint(strict_schema(TooClever)))
    for keyword in ("pattern", "maxLength", "minimum", "maximum"):
        assert keyword in problems


def test_deep_nesting_is_reported():
    assert any("nested" in p for p in lint(strict_schema(TooDeep)))


def test_business_rules_live_in_validators():
    good = {"contact": {"name": "Priya", "company": "Northwind Bakery", "email": "priya@northwind.example"},
            "requests": [{"product_type": "business_card", "amount_usd": 20000, "cards_needed": 12}],
            "annual_revenue_usd": 1800000, "wants_relationship_manager": True, "decision_deadline": "2026-12-15"}
    assert BusinessEnquiry.model_validate(good).requests[0].cards_needed == 12
    bad = {**good, "decision_deadline": "15/12/2026"}
    with pytest.raises(ValidationError):
        BusinessEnquiry.model_validate(bad)
