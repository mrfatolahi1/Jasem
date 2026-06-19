"""Parsing and formatting of human-readable time durations."""

import re

_DURATION_PATTERN = re.compile(
    r"(\d+(?:\.\d+)?)\s*(hours|hour|hrs|hr|h|minutes|minute|mins|min|m)(?![a-z])"
)
"""Matches a number followed by an hour or minute unit, longest spellings first.

The trailing ``(?![a-z])`` lets a unit butt straight up against the next number
(so ``"1h45min"`` reads as both parts) while still rejecting a unit that is only
the start of a longer word (the ``h`` in ``"5 hamburgers"``)."""


def parse_minutes(text):
    """Return the number of minutes described by a free-text duration.

    Understands forms such as ``"2h"``, ``"30 min"``, ``"1h 30min"`` and a bare
    number, which is treated as minutes.

    Args:
        text: Duration text.

    Returns:
        Whole minutes as an int, or ``0`` when nothing parseable is found.
    """
    lowered = (text or "").lower()
    total = 0.0
    for match in _DURATION_PATTERN.finditer(lowered):
        value = float(match[1])
        total += value * 60 if match[2][0] == "h" else value
    if total == 0:
        bare = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*", lowered)
        if bare:
            total = float(bare[1])
    return int(round(total))


def format_minutes(minutes):
    """Render a minute count as a compact ``"1h 30min"`` style string.

    Args:
        minutes: Whole minutes.

    Returns:
        A human-readable duration string.
    """
    hours, remainder = divmod(int(minutes), 60)
    if hours and remainder:
        return f"{hours}h {remainder}min"
    return f"{hours}h" if hours else f"{remainder}min"
