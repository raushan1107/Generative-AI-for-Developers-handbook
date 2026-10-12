"""A scripted stand-in for the OpenAI client, so tests run offline in milliseconds.
Each create() call plays the next "round": either text or tool calls, streamed in small pieces
the way the real API does (including empty-choices chunks and a final usage chunk)."""
import re
import zlib
from types import SimpleNamespace as NS

import httpx
import openai

REQ = httpx.Request("POST", "https://fake.test/openai/v1/chat/completions")


def text(t):
    return {"text": t}


def tool(name, arguments, call_id="call_1"):
    return {"tools": [(call_id, name, arguments)]}


def _chunk(content=None, tool_calls=None, finish=None):
    return NS(usage=None, choices=[NS(delta=NS(content=content, tool_calls=tool_calls), finish_reason=finish)])


class FakeCompletions:
    def __init__(self, rounds, parsed=None):
        self.rounds, self.parsed, self.calls = list(rounds), list(parsed or []), []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        r = self.rounds.pop(0)
        if r.get("raise") == "rate":
            raise openai.RateLimitError("slow down", response=httpx.Response(429, request=REQ), body=None)
        if not kwargs.get("stream"):
            return NS(choices=[NS(message=NS(content=r["text"], refusal=None), finish_reason="stop")])
        return self._stream(r)

    def _stream(self, r):
        yield NS(usage=None, choices=[])                                   # filter-only chunk, like Azure
        if "text" in r:
            for word in r["text"].split(" "):
                yield _chunk(word + " ")
            yield _chunk(finish="stop")
        for index, (call_id, name, arguments) in enumerate(r.get("tools", [])):
            yield _chunk(tool_calls=[NS(index=index, id=call_id, function=NS(name=name, arguments=""))])
            for i in range(0, len(arguments), 7):                          # arguments arrive in fragments
                yield _chunk(tool_calls=[NS(index=index, id=None, function=NS(name=None, arguments=arguments[i:i + 7]))])
        if "tools" in r:
            yield _chunk(finish="tool_calls")
        yield NS(usage=NS(prompt_tokens=100, completion_tokens=10), choices=[])

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        item = self.parsed.pop(0)
        if isinstance(item, Exception):
            raise item
        refusal = item if isinstance(item, str) else None
        return NS(choices=[NS(message=NS(parsed=None if refusal else item, refusal=refusal))])


class FakeEmbeddings:
    """Milestone 5: a deterministic 'embedding' (hashed bag of words), so texts that share
    words get similar vectors. Good enough to test the plumbing; real models capture meaning."""
    DIMS = 256

    def __init__(self):
        self.calls = 0

    def vector(self, text):
        v = [0.0] * self.DIMS
        for word in re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", text.lower()):
            v[zlib.crc32(word.encode()) % self.DIMS] += 1.0
        v[0] += 0.01                                         # never an all-zero vector
        return v

    def create(self, model, input, **kwargs):
        self.calls += 1
        return NS(data=[NS(embedding=self.vector(t)) for t in input])


class FakeClient:
    def __init__(self, rounds=(), parsed=()):
        self.chat = NS(completions=FakeCompletions(rounds, parsed))
        self.embeddings = FakeEmbeddings()
