"""Resolution of natural-language date phrases to ISO calendar dates."""

import calendar
import datetime as dt
import re

from .calendar_view import CalendarView

_WEEKDAYS = {name.lower(): index for index, name in enumerate(calendar.day_name)}
_WEEKDAYS.update({name.lower(): index for index, name in enumerate(calendar.day_abbr)})
"""Weekday names and abbreviations mapped to ``date.weekday()`` indices."""

_MONTHS = {name.lower(): index for index, name in enumerate(calendar.month_name) if name}
_MONTHS.update({name.lower(): index for index, name in enumerate(calendar.month_abbr) if name})
"""Month names and abbreviations mapped to month numbers."""

NO_DATE = {"", "none", "no deadline", "no date", "n/a", "na", "null", "someday", "-"}
"""Phrases that explicitly mean 'no deadline'."""


class DateResolver:
    """Converts temporal phrases into Gregorian ``YYYY-MM-DD`` strings.

    Relative phrases (``tomorrow``, ``next friday``, ``in 3 days``) are calendar
    agnostic. An explicit date the user types is interpreted through the injected
    :class:`~jasem.shared.calendar_view.CalendarView`, so in Jalali mode a typed
    Jalali date is converted to its Gregorian equivalent before storage.
    """

    def __init__(self, calendar=None):
        """Bind the resolver to a calendar view (Gregorian pass-through by default)."""
        self.calendar = calendar or CalendarView(False)

    def resolve(self, phrase, today, llm_date=""):
        """Resolve a phrase to an ISO date relative to ``today``.

        Recognised forms, in priority order: an explicit ISO date anywhere in
        the text; ``in N days/weeks/months``; ``next <weekday>`` (always in the
        future); ``tomorrow``/``yesterday``/``today``; ``next week``/``next
        month``; end-of-week aliases; a bare or ``this`` weekday (today counts);
        and ``<month> <day>`` or ``<day> <month>`` with an optional year.

        Args:
            phrase: The temporal phrase to interpret.
            today: The reference :class:`datetime.date`.
            llm_date: Optional model-supplied ``YYYY-MM-DD`` guess, used as a
                fallback when the phrase itself yields nothing.

        Returns:
            An ISO date string, or an empty string for no deadline.
        """
        fallback = self._iso_or_empty(llm_date)
        text = (phrase or "").strip().lower()
        if text in NO_DATE:
            return fallback

        iso = re.search(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b", text)
        if iso:
            resolved = self.calendar.parse_explicit(int(iso[1]), int(iso[2]), int(iso[3]))
            if resolved:
                return resolved

        offset = re.search(r"\bin\s+(\d+)\s+(day|week|month)s?\b", text)
        if offset:
            count, unit = int(offset[1]), offset[2]
            if unit == "day":
                return (today + dt.timedelta(days=count)).isoformat()
            if unit == "week":
                return (today + dt.timedelta(days=7 * count)).isoformat()
            return self._add_months(today, count).isoformat()

        upcoming = re.search(r"\bnext\s+(\w+)", text)
        if upcoming and upcoming[1] in _WEEKDAYS:
            return self._next_weekday(today, _WEEKDAYS[upcoming[1]], False).isoformat()

        if re.search(r"\btomorrow\b", text):
            return (today + dt.timedelta(days=1)).isoformat()
        if re.search(r"\byesterday\b", text):
            return (today - dt.timedelta(days=1)).isoformat()
        if re.search(r"\b(today|tonight|now)\b", text):
            return today.isoformat()
        if re.search(r"\bnext\s+week\b", text):
            return (today + dt.timedelta(days=7)).isoformat()
        if re.search(r"\bnext\s+month\b", text):
            return self._add_months(today, 1).isoformat()
        if re.search(r"\b(eow|end of week|this week)\b", text):
            return self._next_weekday(today, 4, True).isoformat()

        for name, index in _WEEKDAYS.items():
            if re.search(rf"\b{re.escape(name)}\b", text):
                return self._next_weekday(today, index, True).isoformat()

        month_first = re.search(r"([a-z]+)\s+(\d{1,2})(?:,?\s*(\d{4}))?", text)
        if month_first and month_first[1] in _MONTHS:
            resolved = self._calendar_date(
                month_first[3], _MONTHS[month_first[1]], int(month_first[2]), today
            )
            if resolved:
                return resolved

        day_first = re.search(r"(\d{1,2})\s+([a-z]+)(?:,?\s*(\d{4}))?", text)
        if day_first and day_first[2] in _MONTHS:
            resolved = self._calendar_date(
                day_first[3], _MONTHS[day_first[2]], int(day_first[1]), today
            )
            if resolved:
                return resolved

        return fallback

    def _calendar_date(self, year_text, month, day, today):
        """Build an ISO date from explicit month/day, rolling to next year.

        When no year is given and the date has already passed this year, the
        following year is used.

        Returns:
            The ISO date string, or an empty string when the date is invalid.
        """
        year = int(year_text) if year_text else today.year
        try:
            resolved = dt.date(year, month, day)
        except ValueError:
            return ""
        if not year_text and resolved < today:
            resolved = dt.date(year + 1, month, day)
        return resolved.isoformat()

    @staticmethod
    def _add_months(date, count):
        """Return ``date`` advanced by ``count`` months, clamping the day."""
        month_index = date.month - 1 + count
        year = date.year + month_index // 12
        month = month_index % 12 + 1
        last_day = calendar.monthrange(year, month)[1]
        return dt.date(year, month, min(date.day, last_day))

    @staticmethod
    def _next_weekday(today, target, include_today):
        """Return the next date falling on ``target`` weekday.

        Args:
            today: Reference date.
            target: Target weekday index.
            include_today: Whether today qualifies when it matches ``target``.
        """
        days_ahead = (target - today.weekday()) % 7
        if days_ahead == 0 and not include_today:
            days_ahead = 7
        return today + dt.timedelta(days=days_ahead)

    @staticmethod
    def _iso_or_empty(value):
        """Return ``value`` if it is a valid ISO date, otherwise an empty string."""
        candidate = (value or "").strip()
        return candidate if re.fullmatch(r"\d{4}-\d{2}-\d{2}", candidate) else ""
