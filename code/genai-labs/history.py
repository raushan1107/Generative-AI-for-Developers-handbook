"""Drill 02.6 (reference solution): keep the system message and the most recent turns."""


def trim_history(messages, max_turns):
    """Return a NEW list with the system message (if first) plus the last `max_turns`
    user/assistant pairs. The kept turns never start with an assistant message."""
    if max_turns < 0:
        raise ValueError("max_turns must be >= 0")
    system = [m for m in messages[:1] if m["role"] == "system"]
    rest = messages[len(system):]
    kept = rest[-(max_turns * 2):] if max_turns else []
    while kept and kept[0]["role"] != "user":
        kept = kept[1:]
    return system + kept
