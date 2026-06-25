"""Parsing and formatting of human-readable money amounts."""

import re

_AMOUNT_PATTERN = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*([kmb])?", re.IGNORECASE)
"""Matches the first number in a string, with optional thousands commas, a
decimal part, and a ``k``/``m``/``b`` magnitude suffix (``50k`` -> 50000,
``1.5m`` -> 1500000). Commas are treated as thousands separators."""

_MULTIPLIERS = {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000}


def parse_amount(text):
    """Return the numeric amount described by free-text money text.

    Understands forms such as ``"50000"``, ``"50k"`` (50000), ``"1.5m"``
    (1500000), ``"1,200"`` (1200), and a bare number. The first number found
    anywhere in the text is used, so ``"paid 50k"`` still reads as 50000.

    Args:
        text: Amount text.

    Returns:
        The amount as a float, or ``0.0`` when nothing parseable is found.
    """
    match = _AMOUNT_PATTERN.search((text or "").strip())
    if not match:
        return 0.0
    number = float(match[1].replace(",", ""))
    suffix = (match[2] or "").lower()
    return number * _MULTIPLIERS.get(suffix, 1)


def format_amount(value):
    """Render an amount with thousands separators and no trailing ``.0``.

    Args:
        value: The numeric amount.

    Returns:
        A human-readable amount string, e.g. ``"50,000"`` or ``"1,500,000"``.
    """
    if value == int(value):
        return f"{int(value):,}"
    return f"{value:,.2f}".rstrip("0").rstrip(".")
