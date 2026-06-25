"""Tests for the CalendarView display/input boundary."""

import datetime as dt
import unittest

from jasem.shared.calendar_view import CalendarView
from jasem.shared.config import Config


class GregorianModeTests(unittest.TestCase):
    """When disabled, every method reproduces Gregorian behavior exactly."""

    def setUp(self):
        self.view = CalendarView(False)

    def test_format_iso_passthrough(self):
        """A stored ISO date is shown unchanged; empty stays empty."""
        self.assertEqual(self.view.format_iso("2026-06-25"), "2026-06-25")
        self.assertEqual(self.view.format_iso(""), "")

    def test_labels_match_strftime(self):
        """Timeline labels match the original strftime output."""
        day = dt.date(2026, 6, 19)
        self.assertEqual(self.view.format_day_label(day), day.strftime("%a %m-%d"))
        self.assertEqual(self.view.format_week_label(day), "wk " + day.strftime("%m-%d"))

    def test_parse_explicit_validates_gregorian(self):
        """A valid Gregorian triple parses; an impossible one returns None."""
        self.assertEqual(self.view.parse_explicit(2026, 7, 1), "2026-07-01")
        self.assertIsNone(self.view.parse_explicit(2026, 13, 40))


class JalaliModeTests(unittest.TestCase):
    """When enabled, dates render and parse in the Persian calendar."""

    def setUp(self):
        self.view = CalendarView(True)

    def test_format_iso_to_jalali(self):
        """A stored Gregorian date is shown as its Jalali equivalent."""
        self.assertEqual(self.view.format_iso("2026-06-25"), "1405-04-04")
        self.assertEqual(self.view.format_iso(""), "")

    def test_format_iso_garbage_unchanged(self):
        """A malformed stored value is returned untouched, never raising."""
        self.assertEqual(self.view.format_iso("not-a-date"), "not-a-date")

    def test_day_label_uses_transliterated_weekday(self):
        """The daily label carries a Latin-translit weekday and Jalali month-day."""
        self.assertEqual(self.view.format_day_label(dt.date(2026, 6, 19)), "Jom 03-29")
        self.assertEqual(self.view.format_week_label(dt.date(2026, 6, 19)), "wk 03-29")

    def test_parse_explicit_reads_jalali(self):
        """A typed Jalali date converts to its Gregorian ISO; invalid → None."""
        self.assertEqual(self.view.parse_explicit(1405, 4, 4), "2026-06-25")
        self.assertIsNone(self.view.parse_explicit(1405, 13, 1))


class FromConfigTests(unittest.TestCase):
    """The view reads its mode from the JASEM_JALALI config flag."""

    def test_enabled_from_config(self):
        self.assertTrue(CalendarView.from_config(Config({"JASEM_JALALI": "true"})).enabled)

    def test_disabled_by_default(self):
        self.assertFalse(CalendarView.from_config(Config({})).enabled)


if __name__ == "__main__":
    unittest.main()
