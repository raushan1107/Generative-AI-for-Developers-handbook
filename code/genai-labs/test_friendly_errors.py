"""Tests for friendly_errors.describe_error. Run with:  pytest -q test_friendly_errors.py"""
import httpx
import openai
import pytest

from friendly_errors import describe_error

REQUEST = httpx.Request("POST", "https://example.test/openai/v1/chat/completions")


def status_error(cls, status):
    return cls("boom", response=httpx.Response(status, request=REQUEST), body=None)


@pytest.mark.parametrize("exc, code, retryable", [
    (status_error(openai.RateLimitError, 429), "rate_limited", True),
    (status_error(openai.BadRequestError, 400), "bad_request", False),
    (status_error(openai.AuthenticationError, 401), "config", False),
    (status_error(openai.PermissionDeniedError, 403), "config", False),
    (status_error(openai.NotFoundError, 404), "config", False),
    (status_error(openai.InternalServerError, 503), "server", True),
    (openai.APITimeoutError(request=REQUEST), "unreachable", True),
    (openai.APIConnectionError(request=REQUEST), "unreachable", True),
])
def test_maps_sdk_errors(exc, code, retryable):
    got_code, got_retryable, message = describe_error(exc)
    assert (got_code, got_retryable) == (code, retryable)
    assert message and "Traceback" not in message and "deployment" not in message


def test_unknown_errors_are_not_retried():
    assert describe_error(ValueError("surprise"))[:2] == ("unknown", False)
