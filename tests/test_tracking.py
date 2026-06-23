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
from jasem.domain.time_entry import TimeEntry
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
        self.assertEqual(entries[0].id, 1)


class TrackManageTests(unittest.TestCase):
    """Editing and removing existing time entries via ``jasem track``."""

    def setUp(self):
        """Create a temp log and an app sharing one recording console."""
        self.tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmpdir)
        self.config = Config({
            "JASEM_TRACK_FILE": os.path.join(self.tmpdir, "timelog.md"),
            "JASEM_FILE": os.path.join(self.tmpdir, "tasks.md"),
        })
        self.console = RecordingConsole()
        self.app = App(self.config, self.console)

    def _seed(self):
        """Persist two known entries with ids 1 and 2."""
        self.app.timelog.save([
            TimeEntry(id=1, date="2026-06-19", time_text="1h", work="debugging", tag="work"),
            TimeEntry(id=2, date="2026-06-18", time_text="30min", work="emails", tag="work"),
        ])

    def _entry(self, identifier):
        """Return the reloaded entry with ``identifier``."""
        return next(e for e in self.app.timelog.load() if e.id == identifier)

    def test_add_assigns_incrementing_ids(self):
        """Successive logged entries receive 1, 2, … via ``next_id``."""
        provider = FakeProvider(
            {"minutes": 60, "work": "a", "date_phrase": "today", "date": "", "tag": "work"}
        )
        self.app.time_parser._provider_factory = lambda config: provider
        self.app.run(["track", "1h a today"])
        self.app.run(["track", "1h a today"])
        self.assertEqual([e.id for e in self.app.timelog.load()], [1, 2])

    def test_rm_removes_entry(self):
        """``track rm`` drops the matching id and keeps the rest."""
        self._seed()
        self.app.run(["track", "rm", "1"])
        self.assertEqual([e.id for e in self.app.timelog.load()], [2])

    def test_rm_unknown_id_keeps_everything(self):
        """An id that matches nothing leaves the log untouched."""
        self._seed()
        self.app.run(["track", "rm", "99"])
        self.assertEqual(len(self.app.timelog.load()), 2)

    def test_set_work(self):
        """``track set <id> work …`` joins the remaining words."""
        self._seed()
        self.app.run(["track", "set", "1", "work", "fixing", "the", "parser"])
        self.assertEqual(self._entry(1).work, "fixing the parser")

    def test_set_time_normalises(self):
        """A parseable duration is stored in canonical form."""
        self._seed()
        self.app.run(["track", "set", "2", "time", "90min"])
        self.assertEqual(self._entry(2).time_text, "1h 30min")

    def test_set_time_unparseable_warns_and_stores_raw(self):
        """An unreadable duration is kept as-is and a warning is emitted."""
        self._seed()
        self.app.run(["track", "set", "2", "time", "ages"])
        self.assertEqual(self._entry(2).time_text, "ages")
        self.assertTrue(self.console.warnings)

    def test_set_date_resolves(self):
        """An ISO date is accepted for the date field."""
        self._seed()
        self.app.run(["track", "set", "1", "date", "2026-07-01"])
        self.assertEqual(self._entry(1).date, "2026-07-01")

    def test_set_tag(self):
        """The tag field takes a single category."""
        self._seed()
        self.app.run(["track", "set", "1", "tag", "personal"])
        self.assertEqual(self._entry(1).tag, "personal")


if __name__ == "__main__":
    unittest.main()
