"""Chat service: conversation memory, streaming, error handling and usage logging.
Kept separate from the web layer so it can be used from the CLI, the API and tests."""
import time
import uuid

import openai

from app.config import MAX_TURNS_KEPT, MODEL
from app.llm import get_client
from app.logging_utils import cost_usd, log_event
from app.prompts import SYSTEM_PROMPT

FRIENDLY = {
    "rate_limited": "Traincrest Assist is very busy right now. Please try again in a moment.",
    "unreachable": "I couldn't reach the AI service. Please try again.",
    "bad_request": "I couldn't process that message. Could you rephrase it?",
    "config": "Traincrest Assist is temporarily unavailable. Our team has been notified.",
    "server": "Something went wrong on our side. Please try again shortly.",
}


class ChatService:
    def __init__(self, client=None):
        self.client = client or get_client()
        # session_id -> list of messages. In memory for now; Module 08 moves this to a database.
        self.sessions: dict[str, list[dict]] = {}

    def reset(self, session_id: str) -> None:
        self.sessions.pop(session_id, None)

    def stream(self, session_id: str, user_message: str):
        """Yield events for one turn: {"type": "delta", "text": ...} while the answer streams,
        then exactly one {"type": "done", ...} or {"type": "error", "message": ...}."""
        history = self.sessions.setdefault(session_id, [])
        history[:] = history[-(MAX_TURNS_KEPT * 2):]            # keep whole user/assistant pairs
        history.append({"role": "user", "content": user_message})
        turn_id, start = uuid.uuid4().hex[:8], time.perf_counter()
        ttft, parts, usage, finish = None, [], None, None
        error, detail = None, ""

        try:
            stream = self.client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history,
                stream=True,
                stream_options={"include_usage": True},
            )
            for chunk in stream:
                if chunk.usage:                                  # final chunk carries token usage
                    usage = chunk.usage
                if not chunk.choices:                            # filter-only or usage-only chunks
                    continue
                choice = chunk.choices[0]
                finish = choice.finish_reason or finish
                if choice.delta.content:
                    ttft = ttft or time.perf_counter() - start
                    parts.append(choice.delta.content)
                    yield {"type": "delta", "text": choice.delta.content}
        except openai.RateLimitError as e:
            error, detail = "rate_limited", str(e)
        except openai.APIConnectionError as e:                   # includes timeouts
            error, detail = "unreachable", str(e)
        except openai.BadRequestError as e:
            error, detail = "bad_request", str(e)
        except (openai.AuthenticationError, openai.PermissionDeniedError, openai.NotFoundError) as e:
            error, detail = "config", str(e)
        except openai.APIStatusError as e:
            error, detail = "server", str(e)

        if error:
            history.pop()                                        # forget the unanswered question
            log_event(turn=turn_id, session=session_id[:8], level="error", error=error, detail=detail[:200])
            yield {"type": "error", "message": FRIENDLY[error]}
            return

        reply = "".join(parts)
        history.append({"role": "assistant", "content": reply})
        cost = cost_usd(usage)
        event = {
            "type": "done",
            "finish_reason": finish,
            "ttft_s": round(ttft or 0, 2),
            "total_s": round(time.perf_counter() - start, 2),
            "tokens_in": getattr(usage, "prompt_tokens", None),
            "tokens_out": getattr(usage, "completion_tokens", None),
            "cost_usd": round(cost, 6) if cost is not None else None,
        }
        log_event(turn=turn_id, session=session_id[:8], level="info", model=MODEL,
                  **{k: v for k, v in event.items() if k != "type"})
        yield event
