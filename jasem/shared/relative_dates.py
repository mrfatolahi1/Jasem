"""Human-friendly relative phrasing of stored ISO dates.

All jasem dates are stored as Gregorian ``YYYY-MM-DD`` strings, so the day
arithmetic here is calendar-agnostic: the same number of days separates two
dates whether they are shown in Gregorian or Jalali. Callers pair the phrase
returned here with an absolute date formatted through
:class:`~jasem.shared.calendar_view.CalendarView`.
"""

import datetime as dt


def _days_between(iso, today_iso):
    """Return ``iso - today`` in whole days, or ``None`` if either is unparseable."""
    try:
        target = dt.date.fromisoformat(iso)
        today = dt.date.fromisoformat(today_iso)
    except (ValueError, TypeError):
        return None
    return (target - today).days


def relative_day(iso, today_iso):
    """Return a short relative phrase for a deadline date relative to today.

    Examples: ``overdue`` (past), ``today``, ``tomorrow``, ``in 4d``,
    ``yesterday``, ``3d ago``. Returns ``""`` for an empty or malformed date so
    callers can fall back to an absolute date.
    """
    days = _days_between(iso, today_iso)
    if days is None:
        return ""
    if days < -1:
        return "overdue"
    if days == -1:
        return "yesterday"
    if days == 0:
        return "today"
    if days == 1:
        return "tomorrow"
    if days <= 13:
        return f"in {days}d"
    if days <= 70:
        return f"in {round(days / 7)}w"
    return f"in {round(days / 30)}mo"


def age(iso, today_iso):
    """Return a compact 'how long ago' phrase for a creation date.

    Examples: ``today``, ``1d``, ``6d``, ``3w``, ``5mo``, ``2y``. Returns ``""``
    for an empty or malformed date.
    """
    days = _days_between(iso, today_iso)
    if days is None:
        return ""
    days = -days
    if days <= 0:
        return "today"
    if days < 7:
        return f"{days}d"
    if days < 70:
        return f"{round(days / 7)}w"
    if days < 365:
        return f"{round(days / 30)}mo"
    return f"{round(days / 365)}y"
