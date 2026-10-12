"""Drill 02.13 (reference solution): a reusable retry decorator with exponential backoff and jitter."""
import functools
import random
import time


def retry(retry_on, max_attempts=5, base=1.0, cap=30.0, sleep=time.sleep):
    """Retry the wrapped function when it raises one of the `retry_on` exceptions.

    Waits base * 2**(attempt-1) seconds (never more than `cap`) plus up to 25% random
    jitter between attempts, and re-raises after `max_attempts`. `sleep` is injectable
    so tests can run instantly.
    """
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except retry_on:
                    if attempt == max_attempts:
                        raise
                    wait = min(cap, base * 2 ** (attempt - 1))
                    sleep(wait + random.uniform(0, wait * 0.25))
        return wrapper
    return decorator
