"""The single calendar-aware boundary between stored Gregorian dates and the user.

Everything jasem stores and computes with is Gregorian ISO (``YYYY-MM-DD``). When
Jalali mode is enabled this view renders those dates in the Persian calendar and
interprets explicit dates the user types as Jalali. When disabled every method is a
faithful pass-through, so behavior is identical to a Gregorian-only jasem.
"""

import datetime as dt

from . import jalali


class CalendarView:
    """Formats stored Gregorian dates for display and parses user-typed dates."""

    def __init__(self, enabled):
        """Bind the view to a mode.

        Args:
            enabled: When true, display Jalali and parse explicit input as Jalali.
        """
        self.enabled = bool(enabled)

    @classmethod
    def from_config(cls, config):
        """Build the view from a :class:`~jasem.shared.config.Config`."""
        return cls(config.jalali)

    def format_iso(self, iso_str):
        """Return ``iso_str`` (a stored Gregorian ISO date) as a display string.

        Empty input stays empty so callers keep their ``"—"``/``"no deadline"``
        rules. A malformed string is returned unchanged rather than raising, so
        hand-edited data never crashes rendering.
        """
        if not self.enabled or not iso_str:
            return iso_str
        try:
            date = dt.date.fromisoformat(iso_str)
        except ValueError:
            return iso_str
        jy, jm, jd = jalali.gregorian_to_jalali(date)
        return f"{jy:04d}-{jm:02d}-{jd:02d}"

    def format_day_label(self, date):
        """Return a timeline day label for a :class:`datetime.date`.

        Gregorian: ``"Fri 06-19"``. Jalali: ``"Jom 04-04"`` (Latin-transliterated
        weekday, Jalali month-day).
        """
        if not self.enabled:
            return date.strftime("%a %m-%d")
        jy, jm, jd = jalali.gregorian_to_jalali(date)
        return f"{jalali.JALALI_WEEKDAY_ABBR[date.weekday()]} {jm:02d}-{jd:02d}"

    def format_week_label(self, date):
        """Return a timeline week label for a week-start :class:`datetime.date`.

        Gregorian: ``"wk 06-16"``. Jalali: ``"wk 04-04"`` (Jalali month-day).
        """
        if not self.enabled:
            return "wk " + date.strftime("%m-%d")
        _, jm, jd = jalali.gregorian_to_jalali(date)
        return f"wk {jm:02d}-{jd:02d}"

    def parse_explicit(self, year, month, day):
        """Resolve an explicit ``YYYY-MM-DD`` the user typed to a Gregorian ISO date.

        Gregorian mode validates the triple directly; Jalali mode interprets it as
        a Jalali date and converts. Returns the Gregorian ISO string, or ``None``
        when the date does not exist (so the caller can keep trying other forms).
        """
        try:
            if self.enabled:
                return jalali.jalali_to_gregorian(year, month, day).isoformat()
            return dt.date(year, month, day).isoformat()
        except ValueError:
            return None
