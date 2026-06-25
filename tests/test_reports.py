"""Tests for time-report aggregation, bar charts, and the report command."""

import datetime as dt
import io
import os
import shutil
import tempfile
import unittest

from jasem.application.app import App
from jasem.application.reports import build_report
from jasem.domain.time_entry import TimeEntry
from jasem.shared.calendar_view import CalendarView
from jasem.shared.charts import BAR_WIDTH, bar
from jasem.shared.config import Config
from jasem.shared.console import Console


class BarTests(unittest.TestCase):
    """The Unicode bar renders proportionally and degrades safely."""

    def test_empty_when_no_value(self):
        """A zero value draws nothing."""
        self.assertEqual(bar(0, 10), "")

    def test_empty_when_no_max(self):
        """A zero maximum draws nothing rather than dividing by zero."""
        self.assertEqual(bar(5, 0), "")

    def test_full_bar_at_max(self):
        """A value equal to the maximum fills the whole width."""
        self.assertEqual(bar(10, 10), "█" * BAR_WIDTH)

    def test_half_bar(self):
        """Half the maximum fills half the width with full blocks."""
        self.assertEqual(bar(5, 10), "█" * (BAR_WIDTH // 2))

    def test_length_is_monotonic(self):
        """Larger values never produce a shorter bar."""
        widths = [len(bar(value, 100)) for value in range(0, 101, 7)]
        self.assertEqual(widths, sorted(widths))


def _entries():
    """Return a fixed mix of entries, including one with no parseable time."""
    return [
        TimeEntry(id=1, date="2026-06-19", time_text="1h", work="api", tag="work"),
        TimeEntry(id=2, date="2026-06-19", time_text="30min", work="emails", tag="admin"),
        TimeEntry(id=3, date="2026-06-18", time_text="2h", work="API", tag="work"),
        TimeEntry(id=4, date="2026-06-18", time_text="huh", work="thinking", tag="work"),
    ]


class BuildReportTests(unittest.TestCase):
    """``build_report`` aggregates totals, breakdowns, and the timeline."""

    def _report(self, **kwargs):
        """Build a week-long report over the fixed sample entries."""
        return build_report(
            _entries(), "2026-06-13", "2026-06-19", "2026-06-19",
            "last 7 days", **kwargs
        )

    def test_totals_skip_unparseable_durations(self):
        """Only positive, readable durations count toward the totals."""
        report = self._report()
        self.assertEqual(report.total_minutes, 210)
        self.assertEqual(report.entry_count, 3)
        self.assertEqual(report.active_days, 2)
        self.assertEqual(report.span_days, 7)

    def test_by_tag_sorted_by_minutes(self):
        """Tags are totalled and ordered from most to least time."""
        self.assertEqual(self._report().by_tag, [("work", 180), ("admin", 30)])

    def test_busiest_day_and_average(self):
        """The busiest day and per-active-day average are computed."""
        report = self._report()
        self.assertEqual(report.busiest_day, ("2026-06-18", 120))
        self.assertEqual(report.avg_per_active_day, 105)

    def test_top_activities_group_case_insensitively(self):
        """``api`` and ``API`` collapse into one ranked activity."""
        report = self._report()
        self.assertEqual(report.top_activities[0], ("api", 180, 2))
        self.assertIn(("emails", 30, 1), report.top_activities)

    def test_daily_timeline_fills_the_span(self):
        """A short span yields one zero-filled bucket per day."""
        report = self._report()
        self.assertEqual(report.timeline_unit, "day")
        self.assertEqual(len(report.timeline), 7)
        self.assertEqual(report.timeline[-1][1], 90)
        self.assertEqual(report.timeline[0][1], 0)

    def test_long_span_switches_to_weekly_buckets(self):
        """A span beyond a month is bucketed by week to stay readable."""
        report = build_report(
            _entries(), "2026-01-01", "2026-06-19", "2026-06-19", "all time"
        )
        self.assertEqual(report.timeline_unit, "week")
        self.assertGreater(len(report.timeline), 4)

    def test_empty_period_is_blank(self):
        """No entries means zero totals and no busiest day."""
        report = build_report([], "2026-06-13", "2026-06-19", "2026-06-19", "last 7 days")
        self.assertEqual(report.total_minutes, 0)
        self.assertEqual(report.entry_count, 0)
        self.assertIsNone(report.busiest_day)

    def test_jalali_labels_keep_gregorian_maths(self):
        """A Jalali calendar formats labels while the figures stay Gregorian."""
        report = build_report(
            _entries(), "2026-06-18", "2026-06-19", "2026-06-19",
            "last 7 days", calendar=CalendarView(True)
        )
        self.assertEqual(report.start, "2026-06-18")
        self.assertEqual(report.end, "2026-06-19")
        self.assertEqual(report.busiest_day, ("2026-06-18", 120))
        labels = [label for label, _ in report.timeline]
        self.assertEqual(labels, ["Panj 03-28", "Jom 03-29"])


class ReportCommandTests(unittest.TestCase):
    """End-to-end ``jasem report`` rendering against a temporary log file."""

    def setUp(self):
        """Create a temp log and an app writing to an in-memory console."""
        self.tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmpdir)
        self.config = Config({
            "JASEM_TRACK_FILE": os.path.join(self.tmpdir, "timelog.md"),
            "JASEM_FILE": os.path.join(self.tmpdir, "tasks.md"),
        })
        self.console = Console(io.StringIO())
        self.app = App(self.config, self.console)

    def _output(self):
        """Return everything written to the console so far."""
        return self.console.stream.getvalue()

    def test_report_renders_all_sections(self):
        """A populated week report shows the title, totals, tags, and bars."""
        today = dt.date.today()
        yesterday = today - dt.timedelta(days=1)
        self.app.timelog.save([
            TimeEntry(id=1, date=today.isoformat(), time_text="1h", work="api work", tag="work"),
            TimeEntry(id=2, date=yesterday.isoformat(), time_text="30min", work="emails", tag="admin"),
        ])
        self.app.run(["report", "week"])
        out = self._output()
        self.assertIn("Time report — last 7 days", out)
        self.assertIn("total", out)
        self.assertIn("1h 30min", out)
        self.assertIn("#work", out)
        self.assertIn("Top activities", out)
        self.assertIn("█", out)

    def test_report_filters_by_tag(self):
        """A trailing tag scopes the report and labels the title."""
        today = dt.date.today().isoformat()
        self.app.timelog.save([
            TimeEntry(id=1, date=today, time_text="1h", work="api", tag="work"),
            TimeEntry(id=2, date=today, time_text="2h", work="emails", tag="admin"),
        ])
        self.app.run(["report", "week", "work"])
        out = self._output()
        self.assertIn("#work", out)
        self.assertNotIn("emails", out)

    def test_report_empty_log(self):
        """With nothing tracked the report says so instead of erroring."""
        self.app.run(["report"])
        self.assertIn("nothing tracked", self._output())


if __name__ == "__main__":
    unittest.main()
