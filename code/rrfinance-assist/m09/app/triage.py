"""Ticket triage.
Milestone 3: the model returned JSON, Pydantic validated it, one repair attempt.
Milestone 4: structured outputs. The schema is enforced by the API, so the shape is guaranteed;
business rules (ID format, summary length) are checked by validators in our code.
If the provider doesn't support structured outputs, we fall back to the milestone 3 method."""
import re
from typing import Literal, Optional

import openai
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from app.config import MODEL
from app.guard import neutralise_tags
from app.prompts import render

CUSTOMER_ID = re.compile(r"RR-\d{5}")
# Small models follow the system role more strictly than instructions buried in a long user message.
SYSTEM = "You are a classification service. You reply with one JSON object only: never code, never explanations."


class Triage(BaseModel):
    model_config = ConfigDict(extra="forbid")          # unexpected keys are an error, not a surprise

    # No pattern/max_length here: Azure structured outputs doesn't support them. Validators below do the job.
    customer_name: Optional[str] = Field(description="First name if given, else null")
    customer_id: Optional[str] = Field(description="Like RR-12345, only if it appears in the message, else null")
    product: Optional[str] = Field(description="Product or card name if mentioned, else null")
    issue_category: Literal["card", "dispute", "fraud", "fees", "transfers", "loans", "account", "other"]
    sentiment: Literal["positive", "neutral", "negative"]
    urgency: Literal["low", "medium", "high"]
    summary: str = Field(description="English, at most 20 words")

    @field_validator("customer_id")
    @classmethod
    def customer_id_format(cls, v):
        if v is not None and not CUSTOMER_ID.fullmatch(v):
            raise ValueError("customer_id must look like RR-12345")
        return v

    @field_validator("summary")
    @classmethod
    def summary_length(cls, v):
        if len(v) > 200:
            raise ValueError("summary must be at most 200 characters")
        return v


class TriageError(Exception):
    """The model didn't return a valid triage result."""


def triage(client, message: str, max_attempts: int = 2):
    """Return (Triage, prompt_version, attempts_used)."""
    prompt, version = render("triage", message=neutralise_tags(message))
    problem = ""
    for attempt in range(1, max_attempts + 1):
        try:
            completion = client.chat.completions.parse(
                model=MODEL, response_format=Triage,
                messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}])
        except openai.BadRequestError:
            return _triage_json_repair(client, message)       # provider/model without structured outputs
        except openai.LengthFinishReasonError:
            problem = "the answer was cut off"
            continue
        except openai.ContentFilterFinishReasonError:
            raise TriageError("the content filter blocked the answer") from None
        except ValidationError as e:                          # shape was fine; a business rule failed
            problem = e.errors()[0]["msg"]
            continue
        msg = completion.choices[0].message
        if msg.refusal:
            raise TriageError(f"model refused: {msg.refusal[:100]}")
        return msg.parsed, version, attempt
    raise TriageError(f"no valid result after {max_attempts} attempts: {problem}")


def _triage_json_repair(client, message: str, max_attempts: int = 2):
    """Milestone 3's approach: ask for JSON in the prompt, validate, repair once."""
    prompt, version = render("triage_fallback", message=neutralise_tags(message))
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}]
    problem = ""
    for attempt in range(1, max_attempts + 1):
        response = client.chat.completions.create(model=MODEL, messages=messages)
        text = (response.choices[0].message.content or "").strip()
        try:
            return Triage.model_validate_json(text), version, attempt
        except ValidationError as e:
            first = e.errors()[0]
            problem = f"{'.'.join(str(p) for p in first.get('loc', ())) or 'the output'}: {first['msg']}"
            messages += [{"role": "assistant", "content": text},
                         {"role": "user", "content": f"That output is invalid ({problem}). "
                                                     "Return only the corrected JSON object, with no other text."}]
    raise TriageError(f"invalid JSON after {max_attempts} attempts: {problem}")
