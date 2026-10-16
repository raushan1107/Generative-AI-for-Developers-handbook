"""Chat service: conversation memory, streaming, error handling and usage logging.
Milestone 3 added a versioned system prompt and an output guard.
Milestone 4 adds tools: the model can look things up and create cases, inside a loop we control."""
import time
import uuid
from types import SimpleNamespace

import openai

from app.config import MAX_TOOL_ROUNDS, MAX_TURNS_KEPT, MODEL, TOOL_EXTRAS
from app.guard import check_output
from app.llm import get_client
from app.logging_utils import cost_usd, log_event
from app.prompts import render
from app.tools import LABELS, TOOLS, kit

FRIENDLY = {
    "rate_limited": "RR Finance Assist is very busy right now. Please try again in a moment.",
    "unreachable": "I couldn't reach the AI service. Please try again.",
    "bad_request": "I couldn't process that message. Could you rephrase it?",
    "config": "RR Finance Assist is temporarily unavailable. Our team has been notified.",
    "server": "Something went wrong on our side. Please try again shortly.",
}
SAFE_REPLY = ("Sorry, I can't share that. Could you rephrase your question, "
              "or shall I raise a case for our support team?")
TOO_MANY_STEPS = "Sorry, that took more steps than I'm allowed. Shall I raise a case for our support team?"


class Turn:
    """What we track during one customer turn, across several model calls."""
    def __init__(self):
        self.id, self.start = uuid.uuid4().hex[:8], time.perf_counter()
        self.ttft, self.parts, self.tools = None, [], []
        self.tokens_in = self.tokens_out = None

    def add_usage(self, u):
        if u:
            self.tokens_in = (self.tokens_in or 0) + u.prompt_tokens
            self.tokens_out = (self.tokens_out or 0) + u.completion_tokens


class ChatService:
    def __init__(self, client=None):
        self.client = client or get_client()
        # session_id -> list of user/assistant messages. In memory for now; Module 08 moves this to a database.
        self.sessions: dict[str, list[dict]] = {}

    def reset(self, session_id: str) -> None:
        self.sessions.pop(session_id, None)

    def _model_round(self, messages, turn):
        """One streamed model call. Yields "delta" events as text arrives and returns
        (tool_calls, finish_reason) when the stream ends."""
        stream = self.client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS, parallel_tool_calls=False,
            stream=True, stream_options={"include_usage": True}, **TOOL_EXTRAS)
        calls, finish = {}, None
        for chunk in stream:
            if chunk.usage:
                turn.add_usage(chunk.usage)
            if not chunk.choices:
                continue
            choice = chunk.choices[0]
            finish = choice.finish_reason or finish
            delta = choice.delta
            if delta.content:
                turn.ttft = turn.ttft or time.perf_counter() - turn.start
                turn.parts.append(delta.content)
                yield {"type": "delta", "text": delta.content}
            # Tool calls also arrive in pieces: the id and name first, then the arguments a few characters at a time.
            for part in delta.tool_calls or []:
                slot = calls.setdefault(part.index, {"id": "", "name": "", "arguments": ""})
                slot["id"] = part.id or slot["id"]
                if part.function:
                    slot["name"] += part.function.name or ""
                    slot["arguments"] += part.function.arguments or ""
        return [calls[i] for i in sorted(calls)], finish

    def stream(self, session_id: str, user_message: str, customer_id: str | None = None):
        """Yield events for one turn: "delta" text, "tool" status lines, an optional "replace"
        if the guard blocks the answer, then one "done" or "error" event."""
        system_prompt, prompt_version = render("assist_system")
        history = self.sessions.setdefault(session_id, [])
        history[:] = history[-(MAX_TURNS_KEPT * 2):]            # keep whole user/assistant pairs
        history.append({"role": "user", "content": user_message})
        # This turn's working messages: history plus any tool calls and results. Only the final answer is kept.
        messages = [{"role": "system", "content": system_prompt}] + history
        context = {"customer_id": customer_id}                     # identity comes from the app, not the model
        turn, finish, error, detail = Turn(), None, None, ""

        try:
            for round_no in range(MAX_TOOL_ROUNDS + 1):
                text_before = len(turn.parts)
                calls, finish = yield from self._model_round(messages, turn)   # streams text to the caller
                if not calls:                                    # no tools wanted: the answer is complete
                    break
                if round_no == MAX_TOOL_ROUNDS:                  # the model keeps asking: stop the loop
                    turn.parts = [TOO_MANY_STEPS]
                    yield {"type": "replace", "text": TOO_MANY_STEPS}
                    log_event(turn=turn.id, level="warning", event="tool_limit", rounds=round_no)
                    break
                # Send back the assistant's tool request, then one "tool" message per call with the result.
                messages.append({"role": "assistant", "content": "".join(turn.parts[text_before:]) or None,
                                 "tool_calls": [{"id": c["id"], "type": "function",
                                                 "function": {"name": c["name"], "arguments": c["arguments"]}}
                                                for c in calls]})
                for c in calls:
                    yield {"type": "tool", "name": c["name"], "label": LABELS.get(c["name"], "Working")}
                    result = kit.dispatch(c["name"], c["arguments"], context)
                    ok = not result.startswith('{"error"')
                    turn.tools.append(c["name"] if ok else c["name"] + ":error")
                    log_event(turn=turn.id, session=session_id[:8], level="info" if ok else "warning",
                              event="tool", tool=c["name"], ok=ok, detail=None if ok else result[:160])
                    messages.append({"role": "tool", "tool_call_id": c["id"], "content": result})
        except openai.RateLimitError as e:
            error, detail = "rate_limited", str(e)
        except openai.APIConnectionError as e:
            error, detail = "unreachable", str(e)
        except openai.BadRequestError as e:
            error, detail = "bad_request", str(e)
        except (openai.AuthenticationError, openai.PermissionDeniedError, openai.NotFoundError) as e:
            error, detail = "config", str(e)
        except openai.APIStatusError as e:
            error, detail = "server", str(e)

        if error:
            history.pop()
            log_event(turn=turn.id, session=session_id[:8], level="error", error=error, detail=detail[:200])
            yield {"type": "error", "message": FRIENDLY[error]}
            return

        reply = "".join(turn.parts)
        flagged = check_output(reply)
        if flagged:
            reply = SAFE_REPLY
            yield {"type": "replace", "text": SAFE_REPLY}
        history.append({"role": "assistant", "content": reply})

        cost = cost_usd(SimpleNamespace(prompt_tokens=turn.tokens_in, completion_tokens=turn.tokens_out)
                        if turn.tokens_in is not None else None)
        event = {
            "type": "done",
            "finish_reason": finish,
            "ttft_s": round(turn.ttft or 0, 2),
            "total_s": round(time.perf_counter() - turn.start, 2),
            "tokens_in": turn.tokens_in,
            "tokens_out": turn.tokens_out,
            "cost_usd": round(cost, 6) if cost is not None else None,
            "prompt_version": prompt_version,
            "tools": turn.tools,                                 # new in milestone 4
        }
        log_event(turn=turn.id, session=session_id[:8], level="warning" if flagged else "info", model=MODEL,
                  flagged=flagged, **{k: v for k, v in event.items() if k != "type"})
        yield event
