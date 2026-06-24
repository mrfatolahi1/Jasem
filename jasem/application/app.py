"""The application layer: command handlers wiring the pieces together."""

import datetime as dt
import re

from ..domain.task import PRIORITY_RANK, Task
from ..domain.time_entry import TimeEntry
from ..infrastructure.providers import get_provider
from ..infrastructure.storage import TaskStore, TimeLogStore
from ..interface.help import render_help
from ..interface.presenter import Presenter
from ..shared.dates import DateResolver
from ..shared.durations import format_minutes, parse_minutes
from .parsing import TaskParser, TimeEntryParser

VIEW_NAMES = {"list", "ls", "all", "today", "week", "overdue"}
"""Subcommands that render a filtered list of tasks."""

CLEAR_WORDS = {"none", "no", "clear", "remove", "-", "n/a", "na", "null", ""}
"""Values that mean 'empty this field' when editing a task."""

FIELD_ALIASES = {
    "priority": {"priority", "prio", "p"},
    "deadline": {"deadline", "due", "date", "d"},
    "category": {"category", "categories", "tag", "tags", "c"},
}
"""Accepted aliases for each editable field of ``jasem set``."""

TIME_FIELD_ALIASES = {
    "time": {"time", "duration", "dur", "t"},
    "work": {"work", "desc", "description", "w"},
    "date": {"date", "day", "d"},
    "tag": {"tag", "category", "categories", "c"},
}
"""Accepted aliases for each editable field of ``jasem track set``."""


def resolve_field(name):
    """Return the canonical field name for an alias, or ``None`` if unknown."""
    lowered = name.lower()
    for field, aliases in FIELD_ALIASES.items():
        if lowered in aliases:
            return field
    return None


def resolve_time_field(name):
    """Return the canonical time-entry field for an alias, or ``None``."""
    lowered = name.lower()
    for field, aliases in TIME_FIELD_ALIASES.items():
        if lowered in aliases:
            return field
    return None


class App:
    """Holds the wired collaborators and exposes one method per command."""

    def __init__(self, config, console):
        """Construct stores, parser, and presenter from the given config.

        Args:
            config: The resolved :class:`~jasem.config.Config`.
            console: The output :class:`~jasem.console.Console`.
        """
        self.config = config
        self.console = console
        self.dates = DateResolver()
        self.presenter = Presenter(console)
        self.tasks = TaskStore(config.task_file)
        self.timelog = TimeLogStore(config.track_file)
        self.parser = TaskParser(get_provider, config, self.dates, console)
        self.time_parser = TimeEntryParser(get_provider, config, self.dates, console)

    def run(self, argv):
        """Route a command-line argument list to the matching handler.

        Args:
            argv: Arguments excluding the program name.
        """
        if not argv or argv[0] in ("help", "-h", "--help"):
            self.console.print(render_help(self.console, self.config))
            return
        command, rest = argv[0], argv[1:]
        if command == "tags":
            self.show_tags()
        elif command in VIEW_NAMES:
            self.show_view(command, rest)
        elif command in ("done", "rm"):
            self.complete_or_remove(command, rest)
        elif command in ("set", "edit"):
            self.set_field(rest)
        elif command == "track":
            self.track(rest)
        elif command == "add":
            if not rest:
                self.console.print(self.console.red("usage: jasem add <description>"))
                return
            self.add(" ".join(rest))
        else:
            self.add(" ".join(argv))

    def add(self, text):
        """Parse ``text`` into a task, store it, and report the result."""
        tasks = self.tasks.load()
        task = Task(**self.parser.parse(text))
        task.id = self.tasks.next_id(tasks)
        tasks.append(task)
        self.tasks.save(tasks)
        console = self.console
        console.print(" ".join([console.green("✓ added"), f"#{task.id}:", console.bold(task.title)]))
        detail = f"  priority={task.priority}  deadline={task.deadline or 'no deadline'}"
        if task.tags:
            detail += f"  tags={task.tags}"
        console.print(console.dim(detail))

    def show_view(self, name, filters):
        """Render the named task view, optionally filtered by categories."""
        today = dt.date.today().isoformat()
        week = (dt.date.today() + dt.timedelta(days=7)).isoformat()
        views = {
            "list": (lambda task: not task.done, "Open tasks"),
            "ls": (lambda task: not task.done, "Open tasks"),
            "all": (lambda task: True, "All tasks"),
            "today": (lambda task: not task.done and task.deadline == today, "Due today"),
            "week": (lambda task: not task.done and task.deadline
                     and today <= task.deadline <= week, "Due within 7 days"),
            "overdue": (lambda task: not task.done and task.deadline
                        and task.deadline < today, "Overdue"),
        }
        predicate, header = views[name]
        tasks = [task for task in self.tasks.load() if predicate(task)]
        if filters:
            categories = [item.strip().lower() for item in filters]
            tasks = [task for task in tasks
                     if all(category in task.tag_list() for category in categories)]
            header += "  ·  " + " ".join("#" + category for category in categories)
        self.presenter.tasks(tasks, header, today)

    def complete_or_remove(self, command, rest):
        """Handle ``done``/``rm`` after parsing their integer id arguments."""
        ids = set()
        for argument in rest:
            try:
                ids.add(int(argument))
            except ValueError:
                pass
        if not ids:
            console = self.console
            console.print(console.red(f"usage: jasem {command} <id> [id...]"))
            console.print(console.dim(
                f'  (to add a task that starts with "{command}", quote it: '
                f'jasem add "{command} ...")'
            ))
            return
        if command == "done":
            self.complete(ids)
        else:
            self.remove(ids)

    def complete(self, ids):
        """Mark the tasks with the given ids complete."""
        tasks = self.tasks.load()
        completed = [task for task in tasks if task.id in ids]
        for task in completed:
            task.done = True
        self.tasks.save(tasks)
        console = self.console
        if completed:
            summary = ", ".join(f"#{task.id} {task.title}" for task in completed)
            console.print(console.green("✓ completed:") + " " + summary)
        else:
            console.print(console.red("no matching id(s)"))

    def remove(self, ids):
        """Delete the tasks with the given ids."""
        tasks = self.tasks.load()
        kept = [task for task in tasks if task.id not in ids]
        removed = len(tasks) - len(kept)
        self.tasks.save(kept)
        console = self.console
        console.print(
            console.green(f"✓ removed {removed} task(s)") if removed
            else console.red("no matching id(s)")
        )

    def set_field(self, args):
        """Update one field of a task identified by its id."""
        console = self.console
        if len(args) < 3:
            console.print(console.red("usage: jasem set <id> <priority|deadline|category> <value>"))
            console.print(console.dim("  e.g.  jasem set 3 priority high"))
            console.print(console.dim("        jasem set 3 deadline next friday"))
            console.print(console.dim("        jasem set 3 category work finance     (none clears it)"))
            return
        try:
            identifier = int(args[0])
        except ValueError:
            console.print(console.red(f"not a valid id: {args[0]}"))
            return
        field = resolve_field(args[1])
        if not field:
            console.print(console.red(f"unknown field: {args[1]}"))
            console.print(console.dim("  fields: priority · deadline · category"))
            return
        tasks = self.tasks.load()
        task = next((item for item in tasks if item.id == identifier), None)
        if task is None:
            console.print(console.red(f"no task with id #{identifier}"))
            return
        message = self._apply_field(task, field, " ".join(args[2:]).strip())
        if message is None:
            return
        self.tasks.save(tasks)
        console.print(console.green(f"✓ #{identifier} updated:") + " " + message)
        console.print(console.dim("  " + task.title))

    def _apply_field(self, task, field, value):
        """Apply ``value`` to ``field`` of ``task``.

        Returns:
            A confirmation message, or ``None`` when the value was rejected
            (an explanation has already been printed).
        """
        console = self.console
        if field == "priority":
            lowered = value.lower()
            if lowered not in PRIORITY_RANK:
                console.print(console.red(f"priority must be one of: {', '.join(PRIORITY_RANK)}"))
                return None
            task.priority = lowered
            return f"priority → {lowered}"
        if field == "deadline":
            if value.lower() in CLEAR_WORDS:
                task.deadline = ""
                return "deadline cleared"
            resolved = self.dates.resolve(value, dt.date.today())
            if not resolved:
                console.print(console.red(f"could not understand deadline: {value!r}"))
                console.print(console.dim(
                    "  try: tomorrow · next friday · in 3 days · june 20 · 2026-07-01 · none"
                ))
                return None
            task.deadline = resolved
            return f"deadline → {resolved}"
        if value.lower() in CLEAR_WORDS:
            task.tags = ""
            return "category cleared"
        parts = [part for part in (item.strip() for item in re.split(r"[,\s]+", value)) if part]
        task.tags = ", ".join(parts)
        return f"category → {task.tags}"

    def show_tags(self):
        """Print each category in use on open tasks with its count."""
        counts = {}
        for task in self.tasks.load():
            if task.done:
                continue
            for tag in task.tag_list():
                counts[tag] = counts.get(tag, 0) + 1
        console = self.console
        if not counts:
            console.print(console.dim("  (no categories yet)"))
            return
        console.print(console.bold("Categories — open tasks"))
        for tag, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
            console.print(f"  {count:>3}  " + console.cyan("#" + tag))

    def track(self, args):
        """Dispatch ``jasem track`` to logging, editing, removing, or viewing.

        A bare ``rm``/``set`` first token manages existing entries. Otherwise,
        input that contains a comma or any recognisable duration is logged as a
        new entry (parsed by AI); anything else is treated as a view request,
        optionally scoped by ``today``/``week``/``all`` and a tag filter.
        """
        if args and args[0].lower() in ("rm", "remove", "del", "delete"):
            self._track_remove(args[1:])
            return
        if args and args[0].lower() in ("set", "edit"):
            self._track_set(args[1:])
            return
        text = " ".join(args).strip()
        words = text.split()
        first = words[0].lower() if words else ""
        if "," in text or (first not in ("today", "week", "all") and parse_minutes(text)):
            self._track_add(text)
            return
        period = "today"
        if words and words[0] in ("today", "week", "all"):
            period = words.pop(0)
        tag_filter = words[0].lower() if words else None
        self._track_view(period, tag_filter)

    def _track_add(self, text):
        """Parse a free-text entry with AI and append it to the time log.

        Falls back to the ``<time>, <work>[, <date>][, <tag>]`` comma format
        when the AI backend is unavailable (handled by the parser).
        """
        console = self.console
        today = dt.date.today()
        fields = self.time_parser.parse(text, today)
        minutes = fields.pop("minutes")
        entry = TimeEntry(**fields)
        entries = self.timelog.load()
        entry.id = self.timelog.next_id(entries)
        entries.append(entry)
        self.timelog.save(entries)
        when = "today" if entry.date == today.isoformat() else entry.date
        console.print(" ".join([
            console.green("✓ tracked"), console.bold(entry.time_text), console.dim("·"),
            entry.work, console.dim(f"· {when} · #{entry.tag}"),
        ]))
        if minutes == 0:
            console.warn(console.yellow(
                f"  (couldn't read a duration from {text!r}; "
                "stored as-is, won't count toward totals)"
            ))

    def _track_remove(self, rest):
        """Delete the time entries whose ids appear in ``rest``."""
        console = self.console
        ids = set()
        for argument in rest:
            try:
                ids.add(int(argument))
            except ValueError:
                pass
        if not ids:
            console.print(console.red("usage: jasem track rm <id> [id...]"))
            console.print(console.dim(
                '  (to log work that starts with "rm", quote it: '
                'jasem track "rm ...")'
            ))
            return
        entries = self.timelog.load()
        kept = [entry for entry in entries if entry.id not in ids]
        removed = len(entries) - len(kept)
        self.timelog.save(kept)
        console.print(
            console.green(f"✓ removed {removed} time entr{'y' if removed == 1 else 'ies'}")
            if removed else console.red("no matching id(s)")
        )

    def _track_set(self, args):
        """Update one field of a time entry identified by its id."""
        console = self.console
        if len(args) < 3:
            console.print(console.red("usage: jasem track set <id> <time|work|date|tag> <value>"))
            console.print(console.dim("  e.g.  jasem track set 3 time 1h30min"))
            console.print(console.dim('        jasem track set 3 work "reviewing the PR"'))
            console.print(console.dim("        jasem track set 3 date yesterday"))
            console.print(console.dim("        jasem track set 3 tag personal"))
            return
        try:
            identifier = int(args[0])
        except ValueError:
            console.print(console.red(f"not a valid id: {args[0]}"))
            return
        field = resolve_time_field(args[1])
        if not field:
            console.print(console.red(f"unknown field: {args[1]}"))
            console.print(console.dim("  fields: time · work · date · tag"))
            return
        entries = self.timelog.load()
        entry = next((item for item in entries if item.id == identifier), None)
        if entry is None:
            console.print(console.red(f"no time entry with id #{identifier}"))
            return
        message = self._apply_time_field(entry, field, " ".join(args[2:]).strip())
        if message is None:
            return
        self.timelog.save(entries)
        console.print(console.green(f"✓ #{identifier} updated:") + " " + message)
        console.print(console.dim("  " + entry.work))

    def _apply_time_field(self, entry, field, value):
        """Apply ``value`` to ``field`` of ``entry``.

        Returns:
            A confirmation message, or ``None`` when the value was rejected
            (an explanation has already been printed).
        """
        console = self.console
        if field == "time":
            minutes = parse_minutes(value)
            if minutes > 0:
                entry.time_text = format_minutes(minutes)
                return f"time → {entry.time_text}"
            entry.time_text = value
            console.warn(console.yellow(
                f"  (couldn't read a duration from {value!r}; "
                "stored as-is, won't count toward totals)"
            ))
            return f"time → {value}"
        if field == "date":
            resolved = self.dates.resolve(value, dt.date.today())
            if not resolved:
                console.print(console.red(f"could not understand date: {value!r}"))
                console.print(console.dim(
                    "  try: today · yesterday · last friday · june 20 · 2026-07-01"
                ))
                return None
            entry.date = resolved
            return f"date → {resolved}"
        if field == "tag":
            if value.lower() in CLEAR_WORDS:
                entry.tag = "work"
                return "tag → work"
            entry.tag = value
            return f"tag → {value}"
        entry.work = value
        return f"work → {value}"

    def _track_view(self, period, tag_filter):
        """Render the time log for a period, optionally filtered by tag."""
        entries = self.timelog.load()
        today = dt.date.today()
        today_iso = today.isoformat()
        if period == "all":
            selected, header = entries, "Time log — all"
        elif period == "week":
            since = (today - dt.timedelta(days=6)).isoformat()
            selected = [entry for entry in entries if entry.date >= since]
            header = "Time log — last 7 days"
        else:
            selected = [entry for entry in entries if entry.date == today_iso]
            header = "Time log — today"
        if tag_filter:
            selected = [entry for entry in selected if entry.tag.lower() == tag_filter]
            header += "  ·  #" + tag_filter
        self.presenter.timelog(selected, header, today_iso)
