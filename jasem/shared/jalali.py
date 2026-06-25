"""Conversion between the Gregorian and Persian (Jalali/Shamsi) calendars.

A self-contained, dependency-free implementation of the well-known arithmetic
33-year-cycle algorithm. Used only at jasem's display and input boundaries; all
stored data and internal calculations remain Gregorian.
"""

import datetime as dt

JALALI_WEEKDAY_ABBR = ("Do", "Seh", "Cha", "Panj", "Jom", "Sha", "Yek")
"""Latin transliterations of Persian weekday names, indexed to ``date.weekday()``
(Monday = 0): Doshanbe, Seshanbe, Chaharshanbe, Panjshanbe, Jome, Shanbe, Yekshanbe."""

_GREGORIAN_MONTH_DAYS = (0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334)


def _g_to_j(gy, gm, gd):
    """Convert a Gregorian (year, month, day) to a Jalali ``(jy, jm, jd)`` triple."""
    gy2 = gy + 1 if gm > 2 else gy
    days = (
        355666
        + 365 * gy
        + (gy2 + 3) // 4
        - (gy2 + 99) // 100
        + (gy2 + 399) // 400
        + gd
        + _GREGORIAN_MONTH_DAYS[gm - 1]
    )
    jy = -1595 + 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm = 1 + days // 31
        jd = 1 + days % 31
    else:
        jm = 7 + (days - 186) // 30
        jd = 1 + (days - 186) % 30
    return jy, jm, jd


def _j_to_g(jy, jm, jd):
    """Convert a Jalali ``(jy, jm, jd)`` triple to a Gregorian ``(gy, gm, gd)`` triple."""
    jy += 1595
    days = -355668 + 365 * jy + (jy // 33) * 8 + ((jy % 33) + 3) // 4 + jd
    if jm < 7:
        days += (jm - 1) * 31
    else:
        days += (jm - 7) * 30 + 186
    gy = 400 * (days // 146097)
    days %= 146097
    if days > 36524:
        days -= 1
        gy += 100 * (days // 36524)
        days %= 36524
        if days >= 365:
            days += 1
    gy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        gy += (days - 1) // 365
        days = (days - 1) % 365
    gd = days + 1
    leap = (gy % 4 == 0 and gy % 100 != 0) or (gy % 400 == 0)
    month_days = (0, 31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    gm = 0
    while gm < 13 and gd > month_days[gm]:
        gd -= month_days[gm]
        gm += 1
    return gy, gm, gd


def gregorian_to_jalali(date):
    """Return the Jalali ``(jy, jm, jd)`` for a :class:`datetime.date`."""
    return _g_to_j(date.year, date.month, date.day)


def is_valid_jalali(jy, jm, jd):
    """Return whether ``(jy, jm, jd)`` is a real Jalali date.

    Months 1–6 have 31 days, months 7–11 have 30, and Esfand (12) has 29 days,
    or 30 in a leap year.
    """
    if jm < 1 or jm > 12 or jd < 1:
        return False
    if jm <= 6:
        return jd <= 31
    if jm <= 11:
        return jd <= 30
    return jd <= (30 if _is_jalali_leap(jy) else 29)


def _is_jalali_leap(jy):
    """Return whether ``jy`` is a Jalali leap year (Esfand has 30 days).

    Decided by round-tripping Esfand 30: a non-leap year's Esfand 30 rolls over
    to Farvardin 1 of the next year, so the year fails to round-trip.
    """
    gy, gm, gd = _j_to_g(jy, 12, 30)
    return _g_to_j(gy, gm, gd) == (jy, 12, 30)


def jalali_to_gregorian(jy, jm, jd):
    """Return the :class:`datetime.date` for a Jalali ``(jy, jm, jd)``.

    Raises:
        ValueError: If the Jalali date does not exist.
    """
    if not is_valid_jalali(jy, jm, jd):
        raise ValueError(f"invalid jalali date: {jy}-{jm}-{jd}")
    gy, gm, gd = _j_to_g(jy, jm, jd)
    return dt.date(gy, gm, gd)
