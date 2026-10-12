"""Tests for schema_lint.py and the course enquiry schema. Run:  pytest -q test_schema_lint.py"""
from typing import Optional

import pytest
from pydantic import BaseModel, Field, ValidationError

from course_enquiry import CourseEnquiry
from schema_lint import lint, strict_schema


class TooClever(BaseModel):
    enrolment_id: str = Field(pattern=r"^TC-\d{5}$")       # pattern: not supported
    summary: str = Field(max_length=200)                    # maxLength: not supported
    learners: int = Field(ge=1, le=500)                     # minimum/maximum: not supported


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
    assert lint(strict_schema(CourseEnquiry)) == []


def test_unsupported_keywords_are_reported():
    problems = " ".join(lint(strict_schema(TooClever)))
    for keyword in ("pattern", "maxLength", "minimum", "maximum"):
        assert keyword in problems


def test_deep_nesting_is_reported():
    assert any("nested" in p for p in lint(strict_schema(TooDeep)))


def test_business_rules_live_in_validators():
    good = {"contact": {"name": "Priya", "company": "Northwind", "email": "priya@northwind.example"},
            "requests": [{"topic": "AZ-104", "learners": 12, "preferred_format": "live-online"}],
            "budget_usd": 15000, "wants_private_class": True, "deadline": "2026-12-15"}
    assert CourseEnquiry.model_validate(good).requests[0].learners == 12
    bad = {**good, "deadline": "15/12/2026"}
    with pytest.raises(ValidationError):
        CourseEnquiry.model_validate(bad)
