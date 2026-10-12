"""Drill 04.4 reference solution: a schema for course enquiries from companies.
Shape rules live in the schema; business rules (formats, ranges) live in validators."""
import re
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

Format = Literal["live-online", "classroom", "self-paced", "any"]


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


class CourseRequest(BaseModel):
    topic: str = Field(description="Course or topic requested, in a few words")
    learners: Optional[int] = Field(description="Number of people, or null if not stated")
    preferred_format: Format

    @field_validator("learners")
    @classmethod
    def learners_in_range(cls, v):
        if v is not None and not 1 <= v <= 500:
            raise ValueError("learners must be between 1 and 500")
        return v


class CourseEnquiry(BaseModel):
    contact: Contact
    requests: list[CourseRequest] = Field(description="One entry per course or topic asked about")
    budget_usd: Optional[int] = Field(description="Total budget in US dollars, or null")
    wants_private_class: bool
    deadline: Optional[str] = Field(description="Date training must finish by, as YYYY-MM-DD, or null")

    @field_validator("deadline")
    @classmethod
    def deadline_is_iso_date(cls, v):
        if v is not None and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
            raise ValueError("deadline must be YYYY-MM-DD")
        return v
