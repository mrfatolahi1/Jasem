"""Tests for AI-backed time tracking and duration parsing."""

import datetime as dt
import io
import os
import shutil
import tempfile
import unittest
import urllib.error

from jasem.application.app import App
from jasem.application.parsing import TimeEntryParser
from jasem.infrastructure.providers.base import TIME_ENTRY_SCHEMA
from jasem.shared.config import Config
from jasem.shared.console import Console
from jasem.shared.dates import DateResolver

TODAY = dt.date(2026, 6, 19)


class RecordingConsole(Console):
    """Console that writes nowhere and remembers the warnings it was given."""

    def __init__(self):
        """Bind to a throwaway buffer (color off) and start an empty log."""
        super().__init__(io.StringIO())
        self.warnings = []

    def warn(self, text):
        """Capture a warning instead of writing to stderr."""
        self.warnings.append(text)


class FakeProvider:
    """Stand-in provider returning canned fields or raising a set error."""

    def __init__(self, fields=None, error=None):
        """Configure the reply ``fields`` or the ``error`` to raise."""
        self._fields = fields or {}
        self._error = error
        self.calls = []

    def parse(self, prompt, schema=None):
        """Record the call, then raise the configured error or return fields."""
        self.calls.append((prompt, schema))
        if self._error:
            raise self._error
        return self._fields


def make_parser(provider, env=None):
    """Return a :class:`TimeEntryParser` wired to ``provider``."""
    return TimeEntryParser(
        lambda config: provider, Config(env or {}), DateResolver(), RecordingConsole()
    )


class TimeEntryParserTests(unittest.TestCase):
    """The AI path builds normalised entries and degrades gracefully."""

    def test_normalises_duration_and_applies_defaults(self):
        """Minutes become a canonical ``time_text`` and blanks get defaults."""
        provider = FakeProvider(
            {"minutes": 105, "work": "debugging the parser",
             "date_phrase": "", "date": "", "tag": ""}
        )
        fields = make_parser(provider).parse("1h45min debugging the parser", TODAY)
        self.assertEqual(fields["minutes"], 105)
        self.assertEqual(fields["time_text"], "1h 45min")
        self.assertEqual(fields["work"], "debugging the parser")
        self.assertEqual(fields["tag"], "work")
        self.assertEqual(fields["date"], "2026-06-19")
        self.assertEqual(provider.calls[0][1], TIME_ENTRY_SCHEMA)

    def test_resolves_relative_date_phrase(self):
        """A ``date_phrase`` is resolved relative to today."""
        provider = FakeProvider(
            {"minutes": 120, "work": "coding", "date_phrase": "yesterday",
             "date": "", "tag": "work"}
        )
        fields = make_parser(provider).parse("2h coding yesterday", TODAY)
        self.assertEqual(fields["date"], "2026-06-18")

    def test_coerces_string_minutes(self):
        """Minutes returned as a string are still understood."""
        provider = FakeProvider(
            {"minutes": "90", "work": "x", "date_phrase": "", "date": "", "tag": ""}
        )
        fields = make_parser(provider).parse("90 min x", TODAY)
        self.assertEqual(fields["minutes"], 90)
        self.assertEqual(fields["time_text"], "1h 30min")

    def test_zero_minutes_keeps_raw_text(self):
        """With no duration the original text is stored as-is for visibility."""
        provider = FakeProvider(
            {"minutes": 0, "work": "thinking", "date_phrase": "", "date": "", "tag": ""}
        )
        fields = make_parser(provider).parse("pondering the design", TODAY)
        self.assertEqual(fields["minutes"], 0)
        self.assertEqual(fields["time_text"], "pondering the design")

    def test_falls_back_to_comma_format_when_backend_down(self):
        """A network error degrades to the legacy comma parsing and warns."""
        provider = FakeProvider(error=urllib.error.URLError("offline"))
        console = RecordingConsole()
        parser = TimeEntryParser(lambda config: provider, Config({}), DateResolver(), console)
        fields = parser.parse("1h45min, debugging, yesterday, personal", TODAY)
        self.assertEqual(fields["minutes"], 105)
        self.assertEqual(fields["time_text"], "1h 45min")
        self.assertEqual(fields["work"], "debugging")
        self.assertEqual(fields["date"], "2026-06-18")
        self.assertEqual(fields["tag"], "personal")
        self.assertTrue(console.warnings)


class TrackCommandTests(unittest.TestCase):
    """End-to-end ``jasem track`` add path against a temporary log file."""

    def setUp(self):
        """Create a temp directory and config pointing the log file at it."""
        self.tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmpdir)
        self.config = Config({
            "JASEM_TRACK_FILE": os.path.join(self.tmpdir, "timelog.md"),
            "JASEM_FILE": os.path.join(self.tmpdir, "tasks.md"),
        })

    def test_track_writes_normalised_entry(self):
        """A free-text entry is parsed, normalised, and persisted."""
        app = App(self.config, RecordingConsole())
        provider = FakeProvider(
            {"minutes": 105, "work": "debugging", "date_phrase": "today",
             "date": "", "tag": "work"}
        )
        app.time_parser._provider_factory = lambda config: provider
        app.run(["track", "1h45min debugging today"])
        entries = app.timelog.load()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].time_text, "1h 45min")
        self.assertEqual(entries[0].minutes(), 105)
        self.assertEqual(entries[0].work, "debugging")


if __name__ == "__main__":
    unittest.main()
