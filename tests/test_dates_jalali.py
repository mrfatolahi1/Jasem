"""Tests for DateResolver under the Jalali calendar."""

import datetime as dt
import unittest

from jasem.shared.calendar_view import CalendarView
from jasem.shared.dates import DateResolver

TODAY = dt.date(2026, 6, 19)


class JalaliInputTests(unittest.TestCase):
    """An explicit date the user types is read as Jalali; phrases are unchanged."""

    def setUp(self):
        self.resolver = DateResolver(CalendarView(True))

    def test_explicit_jalali_date_converts_to_gregorian(self):
        """``1405-04-04`` resolves to the stored Gregorian ISO date."""
        self.assertEqual(self.resolver.resolve("1405-04-04", TODAY), "2026-06-25")

    def test_relative_phrases_are_calendar_agnostic(self):
        """Relative phrases produce the same Gregorian ISO as Gregorian mode."""
        gregorian = DateResolver()
        for phrase in ("tomorrow", "next friday", "in 3 days", "yesterday"):
            self.assertEqual(
                self.resolver.resolve(phrase, TODAY),
                gregorian.resolve(phrase, TODAY),
            )

    def test_invalid_jalali_date_falls_through(self):
        """An impossible Jalali date yields no deadline rather than a wrong one."""
        self.assertEqual(self.resolver.resolve("1404-12-30", TODAY), "")


class GregorianInputTests(unittest.TestCase):
    """Default resolver keeps interpreting explicit dates as Gregorian."""

    def test_explicit_iso_date_unchanged(self):
        self.assertEqual(DateResolver().resolve("2026-07-01", TODAY), "2026-07-01")


if __name__ == "__main__":
    unittest.main()
