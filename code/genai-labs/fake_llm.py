"""Module 07: a scripted stand-in for the chat client, so agent tests run offline in milliseconds.
Each create() call returns the next scripted turn: text, or one or more tool calls."""
from types import SimpleNamespace as NS


def says(text):
    return {"text": text}


def calls(name, arguments="{}", call_id="call_1"):
    return {"tools": [(call_id, name, arguments)]}


class FakeLLM:
    def __init__(self, turns):
        self.turns, self.requests = list(turns), []
        self.chat = NS(completions=self)

    def create(self, **kwargs):
        self.requests.append(kwargs)
        turn = self.turns.pop(0) if self.turns else says("(script ended)")
        tool_calls = [NS(id=i, type="function", function=NS(name=n, arguments=a)) for i, n, a in turn.get("tools", [])]
        message = NS(content=turn.get("text"), tool_calls=tool_calls or None)
        return NS(choices=[NS(message=message, finish_reason="tool_calls" if tool_calls else "stop")],
                  usage=NS(total_tokens=100))
