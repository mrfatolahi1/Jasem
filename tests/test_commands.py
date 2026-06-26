"""End-to-end routing tests for the todo/track/acc command namespaces."""

import io
import os
import shutil
import tempfile
import unittest

from jasem.application.app import App
from jasem.domain.task import Task
from jasem.domain.time_entry import TimeEntry
from jasem.shared.config import Config
from jasem.shared.console import Console


class CommandTestCase(unittest.TestCase):
    """Base class wiring an app to a temp data dir and an in-memory console."""

    def setUp(self):
        """Create a throwaway data dir and an app writing to a string buffer."""
        self.tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmpdir)
        self.config = Config({
            "JASEM_FILE": os.path.join(self.tmpdir, "tasks.md"),
            "JASEM_TRACK_FILE": os.path.join(self.tmpdir, "timelog.md"),
            "JASEM_SPEND_FILE": os.path.join(self.tmpdir, "spending.md"),
        })
        self.console = Console(io.StringIO())
        self.app = App(self.config, self.console)

    def _output(self):
        """Return everything written to the console so far."""
        return self.console.stream.getvalue()


class TodoNamespaceTests(CommandTestCase):
    """``jasem todo`` views and manages tasks without needing an AI backend."""

    def _seed(self):
        """Persist two known tasks (ids 1 open, 2 done)."""
        self.app.tasks.save([
            Task(id=1, priority="high", deadline="2026-07-01", title="pay rent", tags="finance"),
            Task(id=2, done=True, priority="low", title="archived note", tags="misc"),
        ])

    def test_bare_todo_lists_open_tasks(self):
        """``jasem todo`` with no args shows the open-task view."""
        self._seed()
        self.app.run(["todo"])
        out = self._output()
        self.assertIn("Open tasks", out)
        self.assertIn("pay rent", out)
        self.assertNotIn("archived note", out)

    def test_todo_aliases_resolve(self):
        """``task``/``tasks`` are accepted as aliases for ``todo``."""
        self._seed()
        self.app.run(["tasks", "list"])
        self.assertIn("pay rent", self._output())

    def test_todo_done_and_rm(self):
        """``todo done``/``todo rm`` complete and delete by id."""
        self._seed()
        self.app.run(["todo", "done", "1"])
        self.assertTrue(next(t for t in self.app.tasks.load() if t.id == 1).done)
        self.app.run(["todo", "rm", "2"])
        self.assertEqual([t.id for t in self.app.tasks.load()], [1])

    def test_todo_set_priority(self):
        """``todo set <id> priority`` edits the task field."""
        self._seed()
        self.app.run(["todo", "set", "1", "priority", "low"])
        self.assertEqual(next(t for t in self.app.tasks.load() if t.id == 1).priority, "low")

    def test_todo_tags_counts_categories(self):
        """``todo tags`` lists categories in use on open tasks."""
        self._seed()
        self.app.run(["todo", "tags"])
        out = self._output()
        self.assertIn("#finance", out)
        self.assertNotIn("#misc", out)  # only open tasks count

    def test_todo_find_matches_title_and_tag(self):
        """``todo find`` matches task titles and tags case-insensitively."""
        self._seed()
        self.app.run(["todo", "find", "RENT"])
        out = self._output()
        self.assertIn('Search · "RENT"', out)
        self.assertIn("pay rent", out)
        self.assertNotIn("archived note", out)


class TrackViewTests(CommandTestCase):
    """``jasem track list`` and ``track tags`` render the time log."""

    def _seed(self):
        """Persist two known time entries."""
        self.app.timelog.save([
            TimeEntry(id=1, date="2026-06-19", time_text="1h", work="api work", tag="work"),
            TimeEntry(id=2, date="2026-06-18", time_text="30min", work="emails", tag="admin"),
        ])

    def test_track_list_shows_entries(self):
        """``track list`` lists logged entries oldest first."""
        self._seed()
        self.app.run(["track", "list"])
        out = self._output()
        self.assertIn("Time entries", out)
        self.assertIn("api work", out)
        self.assertIn("emails", out)

    def test_track_list_filters_by_tag(self):
        """A trailing tag scopes the listing."""
        self._seed()
        self.app.run(["track", "list", "work"])
        out = self._output()
        self.assertIn("api work", out)
        self.assertNotIn("emails", out)

    def test_track_tags_counts_categories(self):
        """``track tags`` lists categories in use across entries."""
        self._seed()
        self.app.run(["track", "tags"])
        out = self._output()
        self.assertIn("#work", out)
        self.assertIn("#admin", out)


class MetaAndLegacyTests(CommandTestCase):
    """Version, help, and migration hints for the pre-namespace commands."""

    def test_version_prints_version(self):
        """``jasem version`` and its flags print the package version."""
        for argv in (["version"], ["--version"], ["-v"]):
            self.console.stream.truncate(0)
            self.console.stream.seek(0)
            self.app.run(argv)
            self.assertRegex(self._output(), r"Jasem \d+\.\d+")

    def test_legacy_report_redirects_without_adding_task(self):
        """A bare ``jasem report`` points at the new path and creates no task."""
        self.app.run(["report"])
        out = self._output()
        self.assertIn("jasem track report", out)
        self.assertEqual(self.app.tasks.load(), [])

    def test_legacy_list_redirects(self):
        """A bare ``jasem list`` points at ``jasem todo list``."""
        self.app.run(["list"])
        self.assertIn("jasem todo list", self._output())

    def test_unknown_command_is_not_added_as_task(self):
        """Unrecognized input is reported, not silently stored as a task."""
        self.app.run(["frobnicate"])
        out = self._output()
        self.assertIn("unknown command", out)
        self.assertEqual(self.app.tasks.load(), [])


if __name__ == "__main__":
    unittest.main()
