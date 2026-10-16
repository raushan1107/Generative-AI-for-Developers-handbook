"""Drill 04.4 reference solution: a schema for business-banking enquiries from companies.
Shape rules live in the schema; business rules (formats, ranges) live in validators."""
import re
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

ProductType = Literal["business_checking", "business_savings", "business_card", "business_loan", "other"]


class Contact(BaseModel):
    name: Optional[str] = Field(description="Person who wrote the enquiry, or null")
    company: Optional[str] = Field(description="Company name, or null")
    email: Optional[str] = Field(description="Email address exactly as written, or null")

    @field_validator("email")
    @classmethod
    def email_looks_valid(cls, v):
        if v is not None and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", v):
            raise ValueError("email is not a valid address")
        return v


class ProductRequest(BaseModel):
    product_type: ProductType
    amount_usd: Optional[int] = Field(description="Loan amount, credit limit or deposit in US dollars, or null")
    cards_needed: Optional[int] = Field(description="Number of employee cards, or null if not stated")

    @field_validator("amount_usd")
    @classmethod
    def amount_in_range(cls, v):
        if v is not None and not 1 <= v <= 5_000_000:
            raise ValueError("amount_usd must be between 1 and 5,000,000")
        return v

    @field_validator("cards_needed")
    @classmethod
    def cards_in_range(cls, v):
        if v is not None and not 1 <= v <= 500:
            raise ValueError("cards_needed must be between 1 and 500")
        return v


class BusinessEnquiry(BaseModel):
    contact: Contact
    requests: list[ProductRequest] = Field(description="One entry per product the company asks about")
    annual_revenue_usd: Optional[int] = Field(description="Company's yearly revenue in US dollars, or null")
    wants_relationship_manager: bool
    decision_deadline: Optional[str] = Field(description="Date the company must decide by, as YYYY-MM-DD, or null")

    @field_validator("decision_deadline")
    @classmethod
    def deadline_is_iso_date(cls, v):
        if v is not None and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
            raise ValueError("decision_deadline must be YYYY-MM-DD")
        return v
