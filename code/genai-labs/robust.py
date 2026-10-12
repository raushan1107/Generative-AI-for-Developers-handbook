"""Drill 04.10: one function that turns every way a structured reply can go wrong
into a clear outcome your code can act on. .parse() does part of this for you;
here you see all of it, and it also works with providers that lack strict mode."""
import re
from dataclasses import dataclass
from typing import Any, Optional

from pydantic import BaseModel, ValidationError

from schema_lint import strict_schema

FENCE = re.compile(r"^```(?:json)?\s*|\s*```$")


@dataclass
class Outcome:
    status: str                  # ok | refused | blocked | truncated | invalid
    value: Optional[Any] = None  # the validated model instance when status == "ok"
    detail: str = ""
    attempts: int = 0


def extract_json(text: str) -> str:
    """Forgive the usual wrapping: code fences and a sentence before or after the object."""
    text = FENCE.sub("", text.strip())
    start, end = text.find("{"), text.rfind("}")
    return text[start:end + 1] if start != -1 and end > start else text


def structured_call(client, model: str, messages: list, schema: type[BaseModel],
                    max_tokens: int = 600, max_attempts: int = 2) -> Outcome:
    response_format = {"type": "json_schema",
                       "json_schema": {"name": schema.__name__, "strict": True, "schema": strict_schema(schema)}}
    messages, problem = list(messages), ""
    for attempt in range(1, max_attempts + 1):
        r = client.chat.completions.create(model=model, messages=messages, response_format=response_format,
                                           max_completion_tokens=max_tokens)
        choice = r.choices[0]
        refusal = getattr(choice.message, "refusal", None)
        if refusal:                                   # the model declined: don't retry, don't parse
            return Outcome("refused", detail=refusal, attempts=attempt)
        if choice.finish_reason == "content_filter":  # the platform's safety filter cut the reply
            return Outcome("blocked", detail="content filter", attempts=attempt)
        if choice.finish_reason == "length":          # ran out of tokens: the JSON is cut off
            problem = f"truncated at {max_tokens} tokens"
            max_tokens *= 2                           # one retry with more room, then give up
            continue
        text = choice.message.content or ""
        try:
            return Outcome("ok", value=schema.model_validate_json(extract_json(text)), attempts=attempt)
        except ValidationError as e:
            first = e.errors()[0]
            problem = f"{'.'.join(map(str, first['loc'])) or 'output'}: {first['msg']}"
            messages += [{"role": "assistant", "content": text},
                         {"role": "user", "content": f"Invalid ({problem}). Return only the corrected JSON object."}]
    status = "truncated" if problem.startswith("truncated") else "invalid"
    return Outcome(status, detail=problem, attempts=max_attempts)
