"""End-to-end routing tests for the todo/track/acc command namespaces."""

import datetime as dt
import io
import os
import shutil
import tempfile
import unittest

from jasem.application.app import App
from jasem.domain.spending import Spending
from jasem.domain.task import Task
from jasem.domain.time_entry import TimeEntry
from jasem.infrastructure.storage import TaskStore, task_lists
from jasem.shared.config import Config
from jasem.shared.console import Console


class CommandTestCase(unittest.TestCase):
    """Base class wiring an app to a temp data dir and an in-memory console."""

    def setUp(self):
        """Create a throwaway data dir and an app writing to a string buffer."""
        self.tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmpdir)
        self.env = {
            "JASEM_FILE": os.path.join(self.tmpdir, "tasks.md"),
            "JASEM_TRACK_FILE": os.path.join(self.tmpdir, "timelog.md"),
            "JASEM_SPEND_FILE": os.path.join(self.tmpdir, "spending.md"),
        }
        self.config = Config(self.env)
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


class OfflineTaskParser:
    """Stand-in task parser so list tests never reach for an AI backend."""

    def parse(self, text, today=None):
        """Return the text as a plain, undated task."""
        return {
            "done": False, "priority": "medium", "deadline": "",
            "title": text, "tags": "", "created": dt.date.today().isoformat(),
        }


class TodoListTests(CommandTestCase):
    """``jasem todo @name`` keeps each named list in its own file."""

    def setUp(self):
        """Wire the base app, then keep task parsing offline."""
        super().setUp()
        self.app.parser = OfflineTaskParser()

    def _path(self, name):
        """Return the file backing the list called ``name``."""
        return task_lists.path_for(self.config.task_file, name)

    def _load(self, name):
        """Return the tasks stored in the list called ``name``."""
        return TaskStore(self._path(name), name).load()

    def _seed(self, name, *titles):
        """Persist one open task per title in the list called ``name``."""
        store = TaskStore(self._path(name), name)
        store.save([Task(id=index, title=title)
                    for index, title in enumerate(titles, start=1)])

    def test_add_creates_a_separate_file(self):
        """Adding to a named list writes a sibling file, not the default one."""
        self.app.run(["todo", "@work", "add", "ship the release"])
        self.assertTrue(os.path.exists(self._path("work")))
        self.assertEqual([t.title for t in self._load("work")], ["ship the release"])
        self.assertEqual(self._load(""), [])
        self.assertIn("created list @work", self._output())

    def test_views_are_scoped_to_the_selected_list(self):
        """A list's view shows its own tasks and no others."""
        self._seed("", "default task")
        self._seed("work", "work task")
        self.app.run(["todo", "@work"])
        out = self._output()
        self.assertIn("@work", out)
        self.assertIn("work task", out)
        self.assertNotIn("default task", out)

    def test_default_view_excludes_named_lists(self):
        """The default list is unaffected by tasks in named lists."""
        self._seed("", "default task")
        self._seed("work", "work task")
        self.app.run(["todo"])
        out = self._output()
        self.assertIn("default task", out)
        self.assertNotIn("work task", out)

    def test_ids_restart_per_list(self):
        """Each list numbers its tasks independently."""
        self._seed("", "default task")
        self.app.run(["todo", "@work", "add", "work task"])
        self.assertEqual([t.id for t in self._load("work")], [1])

    def test_done_and_rm_apply_to_the_selected_list(self):
        """``done`` and ``rm`` act on the selected list only."""
        self._seed("", "default task")
        self._seed("work", "first", "second")
        self.app.run(["todo", "@work", "done", "1"])
        self.assertTrue(self._load("work")[0].done)
        self.app.run(["todo", "@work", "rm", "2"])
        self.assertEqual([t.id for t in self._load("work")], [1])
        self.assertEqual([t.title for t in self._load("")], ["default task"])

    def test_set_and_find_are_scoped(self):
        """``set`` and ``find`` see only the selected list."""
        self._seed("", "pay rent")
        self._seed("work", "pay invoice")
        self.app.run(["todo", "@work", "set", "1", "priority", "high"])
        self.assertEqual(self._load("work")[0].priority, "high")
        self.app.run(["todo", "@work", "find", "pay"])
        out = self._output()
        self.assertIn("pay invoice", out)
        self.assertNotIn("pay rent", out)

    def test_lists_shows_every_list_with_counts(self):
        """``todo lists`` names each list and marks the active one."""
        self._seed("", "default task")
        self._seed("work", "first", "second")
        self.app.run(["todo", "lists"])
        out = self._output()
        self.assertIn("default", out)
        self.assertIn("@work", out)
        self.assertIn("2 open", out)

    def test_move_transfers_with_a_fresh_id(self):
        """``move`` removes from the source and re-numbers in the destination."""
        self._seed("work", "first", "second")
        self._seed("home", "chore")
        self.app.run(["todo", "@work", "move", "1", "home"])
        self.assertEqual([t.title for t in self._load("work")], ["second"])
        self.assertEqual([(t.id, t.title) for t in self._load("home")],
                         [(1, "chore"), (2, "first")])

    def test_move_rejects_the_current_list(self):
        """``move`` into the list you are already in is refused."""
        self._seed("work", "first")
        self.app.run(["todo", "@work", "move", "1", "work"])
        self.assertIn("already in @work", self._output())
        self.assertEqual(len(self._load("work")), 1)

    def test_unknown_list_warns_instead_of_showing_empty(self):
        """A view on a list with no file reports the name rather than nothing."""
        self._seed("work", "first")
        self.app.run(["todo", "@wrok"])
        out = self._output()
        self.assertIn("no list named 'wrok'", out)
        self.assertNotIn("Open tasks", out)

    def test_env_var_sets_the_default_list(self):
        """``JASEM_LIST`` selects a list without an ``@name`` on every command."""
        self._seed("", "default task")
        self._seed("work", "work task")
        app = App(Config(dict(self.env, JASEM_LIST="work")), Console(io.StringIO()))
        app.run(["todo"])
        out = app.console.stream.getvalue()
        self.assertIn("work task", out)
        self.assertNotIn("default task", out)

    def test_at_default_overrides_the_env_var(self):
        """``@default`` returns to the unnamed list when ``JASEM_LIST`` is set."""
        self._seed("", "default task")
        self._seed("work", "work task")
        app = App(Config(dict(self.env, JASEM_LIST="work")), Console(io.StringIO()))
        app.run(["todo", "@default"])
        out = app.console.stream.getvalue()
        self.assertIn("default task", out)
        self.assertNotIn("work task", out)

    def test_invalid_list_name_is_refused(self):
        """A name that could escape the data directory is rejected."""
        self.app.run(["todo", "@../evil", "add", "oops"])
        self.assertIn("invalid list name", self._output())
        self.assertEqual(self._load(""), [])

    def test_quoted_text_starting_with_at_is_a_task(self):
        """A multi-word argument beginning with ``@`` is task text, not a list."""
        self.app.run(["todo", "@ali review the PR"])
        self.assertEqual(len(self._load("")), 1)
        self.assertNotIn("invalid list name", self._output())

    def test_existing_file_without_lists_still_loads(self):
        """A tasks.md written before this feature keeps loading unchanged."""
        with open(self.config.task_file, "w", encoding="utf-8") as handle:
            handle.write(
                "# Tasks\n\n"
                "| ID | ✓ | Priority | Deadline | Task | Tags | Created |\n"
                "| --- | --- | --- | --- | --- | --- | --- |\n"
                "| 1 | ☐ | high | 2026-07-01 | pay rent | finance | 2026-06-15 |\n"
            )
        self.app.run(["todo"])
        self.assertIn("pay rent", self._output())


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


class AccViewTests(CommandTestCase):
    """``jasem acc list`` renders the spending log."""

    def test_acc_list_all_includes_future_dates(self):
        """The ``all`` window spans every record, even ones dated ahead of today."""
        self.app.spending.save([
            Spending(id=1, date="2026-06-20", amount_text="100,000",
                     title="lunch", tag="food"),
            Spending(id=2, date="2647-09-11", amount_text="360,000",
                     title="snack", tag="snacks"),
        ])
        self.app.run(["acc", "list"])
        out = self._output()
        self.assertIn("lunch", out)
        self.assertIn("snack", out)
        self.assertIn("2 records", out)


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
