"""Tests for the Gregorian↔Jalali calendar conversion."""

import datetime as dt
import unittest

from jasem.shared.jalali import (
    gregorian_to_jalali,
    is_valid_jalali,
    jalali_to_gregorian,
)


class ConversionTests(unittest.TestCase):
    """Known anchors and the round-trip property hold."""

    def test_known_anchor(self):
        """A mid-year Gregorian date maps to its documented Jalali date."""
        self.assertEqual(gregorian_to_jalali(dt.date(2026, 6, 25)), (1405, 4, 4))
        self.assertEqual(jalali_to_gregorian(1405, 4, 4), dt.date(2026, 6, 25))

    def test_nowruz(self):
        """The Persian new year (1 Farvardin 1405) is 2026-03-21."""
        self.assertEqual(jalali_to_gregorian(1405, 1, 1), dt.date(2026, 3, 21))
        self.assertEqual(gregorian_to_jalali(dt.date(2026, 3, 21)), (1405, 1, 1))

    def test_round_trip_over_two_centuries(self):
        """Every day across 200 years survives a there-and-back conversion."""
        day = dt.date(1925, 1, 1)
        end = dt.date(2125, 12, 31)
        while day <= end:
            jy, jm, jd = gregorian_to_jalali(day)
            self.assertEqual(jalali_to_gregorian(jy, jm, jd), day)
            day += dt.timedelta(days=1)


class ValidationTests(unittest.TestCase):
    """``is_valid_jalali`` and the leap-year rule for Esfand."""

    def test_leap_year_esfand_thirty_is_valid(self):
        """In a leap Jalali year Esfand has 30 days and round-trips."""
        self.assertTrue(is_valid_jalali(1403, 12, 30))
        date = jalali_to_gregorian(1403, 12, 30)
        self.assertEqual(gregorian_to_jalali(date), (1403, 12, 30))

    def test_non_leap_year_esfand_thirty_raises(self):
        """A non-leap year has no Esfand 30, so conversion is rejected."""
        self.assertFalse(is_valid_jalali(1404, 12, 30))
        with self.assertRaises(ValueError):
            jalali_to_gregorian(1404, 12, 30)

    def test_out_of_range_components(self):
        """Month and day bounds are enforced per the 6/5/1 month-length split."""
        self.assertFalse(is_valid_jalali(1405, 0, 1))
        self.assertFalse(is_valid_jalali(1405, 13, 1))
        self.assertFalse(is_valid_jalali(1405, 1, 0))
        self.assertFalse(is_valid_jalali(1405, 1, 32))
        self.assertFalse(is_valid_jalali(1405, 7, 31))
        self.assertTrue(is_valid_jalali(1405, 6, 31))
        self.assertTrue(is_valid_jalali(1405, 7, 30))


if __name__ == "__main__":
    unittest.main()
