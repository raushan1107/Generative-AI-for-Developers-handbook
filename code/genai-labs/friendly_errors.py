"""Drill 02.11 (reference solution): turn SDK exceptions into decisions and kind messages."""
import openai

MESSAGES = {
    "rate_limited": "Traincrest Assist is very busy right now. Please try again in a moment.",
    "unreachable": "I couldn't reach the AI service. Please check your connection and try again.",
    "bad_request": "I couldn't process that message. Could you rephrase it?",
    "config": "Traincrest Assist is temporarily unavailable. Our team has been notified.",
    "server": "Something went wrong on our side. Please try again shortly.",
    "unknown": "Something unexpected happened. Please try again.",
}


def describe_error(exc):
    """Return (code, retryable, user_message) for an exception raised by the OpenAI SDK."""
    if isinstance(exc, openai.RateLimitError):
        code, retryable = "rate_limited", True
    elif isinstance(exc, openai.APIConnectionError):          # includes APITimeoutError
        code, retryable = "unreachable", True
    elif isinstance(exc, openai.BadRequestError):
        code, retryable = "bad_request", False
    elif isinstance(exc, (openai.AuthenticationError, openai.PermissionDeniedError, openai.NotFoundError)):
        code, retryable = "config", False
    elif isinstance(exc, openai.APIStatusError):
        code, retryable = "server", exc.status_code >= 500
    else:
        code, retryable = "unknown", False
    return code, retryable, MESSAGES[code]
