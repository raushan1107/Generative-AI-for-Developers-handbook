"""Drill 04.10: chaos test. A fake model misbehaves in every common way;
robust.structured_call must turn each case into the right outcome. Offline, no API key."""
from types import SimpleNamespace as NS
from typing import Literal

from pydantic import BaseModel

from robust import structured_call


class Reply(BaseModel):
    category: Literal["billing", "scheduling", "other"]
    urgent: bool


GOOD = '{"category": "billing", "urgent": false}'


def says(content=None, finish="stop", refusal=None):
    return NS(choices=[NS(message=NS(content=content, refusal=refusal), finish_reason=finish)])


class FakeModel:
    """Plays back a list of canned responses, one per call."""
    def __init__(self, *responses):
        self.responses = list(responses)
        self.chat = NS(completions=NS(create=lambda **kw: self.responses.pop(0)))


SCENARIOS = {
    "clean JSON": [says(GOOD)],
    "fenced JSON": [says("```json\n" + GOOD + "\n```")],
    "sentence + JSON": [says("Sure! Here it is: " + GOOD + " Hope that helps.")],
    "wrong value, then fixed": [says('{"category": "refund", "urgent": false}'), says(GOOD)],
    "garbage twice": [says("I think it's billing."), says("billing, not urgent")],
    "cut off, then fixed": [says('{"category": "bil', finish="length"), says(GOOD)],
    "cut off twice": [says('{"cat', finish="length"), says('{"category"', finish="length")],
    "refusal": [says(refusal="I can't help with that request.")],
    "content filter": [says(None, finish="content_filter")],
}

if __name__ == "__main__":
    print(f"{'scenario':<26}{'status':<11}{'tries':<7}detail / value")
    for name, responses in SCENARIOS.items():
        out = structured_call(FakeModel(*responses), "fake", [{"role": "user", "content": "x"}], Reply)
        shown = out.value.model_dump() if out.value else out.detail
        print(f"{name:<26}{out.status:<11}{out.attempts:<7}{shown}")
