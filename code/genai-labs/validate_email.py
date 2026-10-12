"""Drill 03.1 (reference result of the *specified* prompt): a small, testable email validator."""


def validate_email(address: str) -> tuple[bool, str]:
    """Return (is_valid, reason). Rules, deliberately simple and explicit:
    - surrounding whitespace is ignored; spaces inside are not allowed
    - exactly one '@', with a non-empty part on both sides
    - the domain contains a dot, doesn't start or end with one, and has no '..'
    - at most 254 characters in total
    """
    if not isinstance(address, str):
        return False, "not a string"
    value = address.strip()
    if not value:
        return False, "empty"
    if len(value) > 254:
        return False, "too long"
    if " " in value:
        return False, "contains spaces"
    if value.count("@") != 1:
        return False, "must contain exactly one @"
    local, domain = value.split("@")
    if not local:
        return False, "missing name before @"
    if "." not in domain or domain.startswith(".") or domain.endswith(".") or ".." in domain:
        return False, "invalid domain"
    return True, "ok"
