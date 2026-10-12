"""Ticket triage (milestone 3): the model returns JSON, Pydantic validates it,
and we ask the model to repair its answer once if validation fails."""
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.config import MODEL
from app.guard import neutralise_tags
from app.prompts import render


class Triage(BaseModel):
    model_config = ConfigDict(extra="forbid")          # unexpected keys are an error, not a surprise

    learner_name: Optional[str] = None
    enrolment_id: Optional[str] = Field(default=None, pattern=r"^TC-\d{5}$")
    course: Optional[str] = None
    issue_category: Literal["scheduling", "billing", "exam_voucher", "certificate", "lab_access", "account", "other"]
    sentiment: Literal["positive", "neutral", "negative"]
    urgency: Literal["low", "medium", "high"]
    summary: str = Field(max_length=200)


class TriageError(Exception):
    """The model didn't return valid triage JSON, even after a repair attempt."""


def triage(client, message: str, max_attempts: int = 2):
    """Return (Triage, prompt_version, attempts_used)."""
    prompt, version = render("triage", message=neutralise_tags(message))
    messages = [{"role": "user", "content": prompt}]
    problem = ""
    for attempt in range(1, max_attempts + 1):
        response = client.chat.completions.create(model=MODEL, messages=messages)
        text = (response.choices[0].message.content or "").strip()
        try:
            return Triage.model_validate_json(text), version, attempt
        except ValidationError as e:
            first = e.errors()[0]
            where = ".".join(str(p) for p in first.get("loc", ())) or "the output"
            problem = f"{where}: {first['msg']}"
            # Show the model its own answer and the exact problem, and ask for a corrected version.
            messages += [
                {"role": "assistant", "content": text},
                {"role": "user", "content": f"That output is invalid ({problem}). "
                                            "Return only the corrected JSON object, with no other text."},
            ]
    raise TriageError(f"invalid JSON after {max_attempts} attempts: {problem}")
