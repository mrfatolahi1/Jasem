"""Tests for free-text duration parsing."""

import unittest

from jasem.shared.durations import parse_minutes


class DurationParsingTests(unittest.TestCase):
    """Durations with no separator between units must keep every part."""

    def test_glued_units_keep_the_hours(self):
        """``1h45min`` is 105 minutes, not 45 (the old ``\\b`` dropped the hours)."""
        self.assertEqual(parse_minutes("1h45min"), 105)
        self.assertEqual(parse_minutes("2h30min"), 150)
        self.assertEqual(parse_minutes("1h45m"), 105)

    def test_spaced_units_still_work(self):
        """A separator between units is still understood."""
        self.assertEqual(parse_minutes("1h 45min"), 105)
        self.assertEqual(parse_minutes("2h"), 120)

    def test_unit_is_not_matched_inside_a_word(self):
        """A unit letter starting a longer word is not a duration."""
        self.assertEqual(parse_minutes("5 hamburgers"), 0)


if __name__ == "__main__":
    unittest.main()
