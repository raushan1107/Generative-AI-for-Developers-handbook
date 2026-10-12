"""Drill 04.9: validation in layers.
Layer 1, shape: the JSON Schema (strict mode guarantees it).
Layer 2, business rules: Pydantic validators in YOUR code (formats, ranges, dates).
Layer 3, facts: compare what the model says with what your systems say."""
import re
from datetime import date, timedelta
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

ENROLMENT_ID = re.compile(r"TC-\d{5}")


def today() -> date:                     # a function, so tests can pretend it's another day
    return date.today()


class TicketDraft(BaseModel):
    """Arguments the model sends to create_support_ticket."""
    category: Literal["scheduling", "billing", "exam_voucher", "certificate", "lab_access", "account", "other"]
    summary: str = Field(description="One sentence for the support team")
    enrolment_id: Optional[str] = Field(description="Like TC-12345, or null")
    urgency: Literal["low", "medium", "high"]
    preferred_date: Optional[str] = Field(description="New class date the learner wants, YYYY-MM-DD, or null")

    @field_validator("enrolment_id")
    @classmethod
    def enrolment_id_format(cls, v):
        if v is not None and not ENROLMENT_ID.fullmatch(v):
            raise ValueError("enrolment_id must look like TC-12345")
        return v

    @field_validator("summary")
    @classmethod
    def summary_length(cls, v):
        v = v.strip()
        if not 10 <= len(v) <= 200:
            raise ValueError("summary must be 10 to 200 characters")
        return v

    @field_validator("preferred_date")
    @classmethod
    def date_in_next_year(cls, v):
        if v is None:
            return v
        try:
            d = date.fromisoformat(v)
        except ValueError:
            raise ValueError("preferred_date must be YYYY-MM-DD") from None
        if not today() < d <= today() + timedelta(days=365):
            raise ValueError("preferred_date must be in the future and within 365 days")
        return v

    @model_validator(mode="after")
    def scheduling_needs_an_enrolment(self):
        if self.category == "scheduling" and self.enrolment_id is None:
            raise ValueError("a scheduling ticket needs the enrolment_id; ask the learner for it")
        return self


MONEY = re.compile(r"\$\s?(\d[\d,]*(?:\.\d{2})?)")


def unsupported_amounts(answer: str, allowed: set[float]) -> list[float]:
    """Layer 3: dollar amounts in the model's answer that our systems didn't produce."""
    found = {float(m.replace(",", "")) for m in MONEY.findall(answer)}
    return sorted(found - set(allowed))
