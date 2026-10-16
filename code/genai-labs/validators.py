"""Drill 04.9: validation in layers.
Layer 1, shape: the JSON Schema (strict mode guarantees it).
Layer 2, business rules: Pydantic validators in YOUR code (formats, ranges, dates).
Layer 3, facts: compare what the model says with what your systems say."""
import re
from datetime import date, timedelta
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

CUSTOMER_ID = re.compile(r"RR-\d{5}")
MAX_AGE_DAYS = 90                        # older disputes go to a person, not an automatic case


def today() -> date:                     # a function, so tests can pretend it's another day
    return date.today()


class CaseDraft(BaseModel):
    """Arguments the model sends to open_support_case."""
    category: Literal["card", "dispute", "fraud", "fees", "transfers", "loans", "account", "other"]
    summary: str = Field(description="One sentence for the support team")
    customer_id: Optional[str] = Field(description="Like RR-12345, or null")
    urgency: Literal["low", "medium", "high"]
    transaction_date: Optional[str] = Field(description="Date of the payment in question, YYYY-MM-DD, or null")

    @field_validator("customer_id")
    @classmethod
    def customer_id_format(cls, v):
        if v is not None and not CUSTOMER_ID.fullmatch(v):
            raise ValueError("customer_id must look like RR-12345")
        return v

    @field_validator("summary")
    @classmethod
    def summary_length(cls, v):
        v = v.strip()
        if not 10 <= len(v) <= 200:
            raise ValueError("summary must be 10 to 200 characters")
        return v

    @field_validator("transaction_date")
    @classmethod
    def date_in_the_last_90_days(cls, v):
        if v is None:
            return v
        try:
            d = date.fromisoformat(v)
        except ValueError:
            raise ValueError("transaction_date must be YYYY-MM-DD") from None
        if d > today():
            raise ValueError("transaction_date can't be in the future")
        if d < today() - timedelta(days=MAX_AGE_DAYS):
            raise ValueError(f"transaction_date is more than {MAX_AGE_DAYS} days ago; route to a person")
        return v

    @model_validator(mode="after")
    def disputes_need_a_customer(self):
        if self.category in ("dispute", "fraud") and self.customer_id is None:
            raise ValueError(f"a {self.category} case needs the customer_id; ask the customer for it")
        return self


MONEY = re.compile(r"\$\s?(\d[\d,]*(?:\.\d{2})?)")


def unsupported_amounts(answer: str, allowed: set[float]) -> list[float]:
    """Layer 3: dollar amounts in the model's answer that our systems didn't produce."""
    found = {float(m.replace(",", "")) for m in MONEY.findall(answer)}
    return sorted(found - set(allowed))
