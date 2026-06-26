"""The application layer: command handlers wiring the pieces together."""

import datetime as dt
import re

from ..domain.spending import Spending
from ..domain.task import PRIORITY_RANK, Task
from ..domain.time_entry import TimeEntry
from ..infrastructure.providers import get_provider
from ..infrastructure.storage import SpendingStore, TaskStore, TimeLogStore
from ..interface.help import render_help
from ..interface.presenter import Presenter
from ..shared.amounts import format_amount, parse_amount
from ..shared.calendar_view import CalendarView
from ..shared.dates import DateResolver
from ..shared.durations import format_minutes, parse_minutes
from .parsing import SpendingParser, TaskParser, TimeEntryParser
from .reports import build_report, build_spending_report

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

SPEND_FIELD_ALIASES = {
    "amount": {"amount", "amt", "cost", "price", "a"},
    "title": {"title", "text", "name", "t"},
    "description": {"description", "desc", "note", "notes", "details"},
    "date": {"date", "day", "d"},
    "tag": {"tag", "category", "categories", "c"},
}
"""Accepted aliases for each editable field of ``jasem acc set``."""

PERIODS = ("today", "week", "month", "all")
"""Time windows accepted by the ``list`` and ``report`` subcommands."""

LEGACY_HINTS = {
    "list": "todo list", "ls": "todo list", "all": "todo all",
    "today": "todo today", "week": "todo week", "overdue": "todo overdue",
    "tags": "todo tags", "done": "todo done", "rm": "todo rm",
    "set": "todo set", "edit": "todo set", "add": "todo add",
    "find": "todo find", "search": "todo find", "report": "track report",
}
"""Pre-namespace command words mapped to where they live now."""


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


def resolve_spend_field(name):
    """Return the canonical spending field for an alias, or ``None``."""
    lowered = name.lower()
    for field, aliases in SPEND_FIELD_ALIASES.items():
        if lowered in aliases:
            return field
    return None


def resolve_window(dates_present, args, today, default):
    """Split optional ``[period] [tag]`` arguments into a window and tag filter.

    Shared by the ``list`` and ``report`` subcommands of every namespace.

    Args:
        dates_present: ISO dates present in the data set, used to anchor the
            start of an ``all`` window.
        args: The raw argument words following the subcommand.
        today: Today's :class:`datetime.date`.
        default: Period assumed when none is given (``"week"`` for reports,
            ``"all"`` for plain lists).

    Returns:
        A ``(start, end, label, tag_filter)`` tuple — ISO date strings plus an
        optional lowercase tag.
    """
    today_iso = today.isoformat()
    words = list(args)
    period = default
    if words and words[0].lower() in PERIODS:
        period = words.pop(0).lower()
    tag_filter = words[0].lower() if words else None
    if period == "all":
        start, label = min(dates_present, default=today_iso), "all time"
    elif period == "today":
        start, label = today_iso, "today"
    elif period == "month":
        start, label = (today - dt.timedelta(days=29)).isoformat(), "last 30 days"
    else:
        start, label = (today - dt.timedelta(days=6)).isoformat(), "last 7 days"
    return start, today_iso, label, tag_filter


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
        self.calendar = CalendarView.from_config(config)
        self.dates = DateResolver(self.calendar)
        self.presenter = Presenter(console, self.calendar)
        self.tasks = TaskStore(config.task_file)
        self.timelog = TimeLogStore(config.track_file)
        self.spending = SpendingStore(config.spend_file)
        self.parser = TaskParser(get_provider, config, self.dates, console)
        self.time_parser = TimeEntryParser(get_provider, config, self.dates, console)
        self.spend_parser = SpendingParser(get_provider, config, self.dates, console)

    def run(self, argv):
        """Route a command-line argument list to the matching handler.

        Args:
            argv: Arguments excluding the program name.
        """
        if not argv or argv[0].lower() in ("help", "-h", "--help"):
            self.console.print(render_help(self.console, self.config))
            return
        command, rest = argv[0].lower(), argv[1:]
        if command in ("version", "--version", "-v"):
            self.version()
        elif command in ("todo", "task", "tasks"):
            self.todo(rest)
        elif command == "track":
            self.track(rest)
        elif command == "acc":
            self.acc(rest)
        else:
            self.unknown(argv[0])

    def version(self):
        """Print the running jasem version."""
        try:
            from importlib.metadata import version as package_version
            shown = package_version("jasem")
        except Exception:
            from .. import __version__ as shown
        self.console.print(f"jasem {shown}")

    def unknown(self, word):
        """Explain an unrecognized top-level command, redirecting old verbs."""
        console = self.console
        hint = LEGACY_HINTS.get(word.lower())
        if hint:
            console.print(console.red(f"{word!r} is now ") + console.green(f"jasem {hint}"))
        else:
            console.print(console.red(f"unknown command: {word}"))
        console.print(console.dim("  see ") + console.green("jasem help"))

    def todo(self, args):
        """Dispatch ``jasem todo`` to adding, viewing, editing, or searching tasks.

        A bare ``jasem todo`` lists open tasks; a leading view or verb keyword
        manages existing tasks; any other text is added as a new task (parsed by
        AI, falling back to regex when no backend is reachable).
        """
        head = args[0].lower() if args else ""
        if not args:
            self.show_view("list", [])
        elif head == "add":
            text = " ".join(args[1:]).strip()
            if not text:
                self.console.print(self.console.red('usage: jasem todo add "<description>"'))
                return
            self.add(text)
        elif head in VIEW_NAMES:
            self.show_view(head, args[1:])
        elif head == "tags":
            self.show_tags()
        elif head == "done":
            self.complete_or_remove("done", args[1:])
        elif head in ("rm", "remove", "del", "delete"):
            self.complete_or_remove("rm", args[1:])
        elif head in ("set", "edit"):
            self.set_field(args[1:])
        elif head in ("find", "search"):
            self.find(args[1:])
        else:
            self.add(" ".join(args).strip())

    def find(self, args):
        """List tasks whose title or tags contain the given text (case-insensitive)."""
        console = self.console
        query = " ".join(args).strip()
        if not query:
            console.print(console.red('usage: jasem todo find "<text>"'))
            return
        needle = query.lower()
        today = dt.date.today().isoformat()
        matches = [
            task for task in self.tasks.load()
            if needle in task.title.lower() or needle in task.tags.lower()
        ]
        self.presenter.tasks(matches, f'Search · "{query}"', today)

    def add(self, text):
        """Parse ``text`` into a task, store it, and report the result."""
        tasks = self.tasks.load()
        task = Task(**self.parser.parse(text))
        task.id = self.tasks.next_id(tasks)
        tasks.append(task)
        self.tasks.save(tasks)
        console = self.console
        console.print(" ".join([console.green("✓ added"), f"#{task.id}:", console.bold(task.title)]))
        shown_deadline = self.calendar.format_iso(task.deadline) or "no deadline"
        detail = f"  priority={task.priority}  deadline={shown_deadline}"
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
            console.print(console.red(f"usage: jasem todo {command} <id> [id...]"))
            console.print(console.dim(
                f'  (to add a task that starts with "{command}", quote it: '
                f'jasem todo add "{command} ...")'
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
            console.print(console.red("usage: jasem todo set <id> <priority|deadline|category> <value>"))
            console.print(console.dim("  e.g.  jasem todo set 3 priority high"))
            console.print(console.dim("        jasem todo set 3 deadline next friday"))
            console.print(console.dim("        jasem todo set 3 category work finance     (none clears it)"))
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
                example = self.calendar.format_iso("2026-07-01")
                console.print(console.red(f"could not understand deadline: {value!r}"))
                console.print(console.dim(
                    f"  try: tomorrow · next friday · in 3 days · june 20 · {example} · none"
                ))
                return None
            task.deadline = resolved
            return f"deadline → {self.calendar.format_iso(resolved)}"
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
        """Dispatch ``jasem track`` across the time-tracking sub-verbs.

        A leading ``list``/``tags``/``report``/``rm``/``set`` keyword views or
        manages existing entries; any other text is logged as a new entry
        (parsed by AI, with a comma-format fallback when the backend is down).
        """
        head = args[0].lower() if args else ""
        if head in ("rm", "remove", "del", "delete"):
            self._track_remove(args[1:])
            return
        if head in ("set", "edit"):
            self._track_set(args[1:])
            return
        if head in ("list", "ls"):
            self._track_list(args[1:])
            return
        if head == "tags":
            self._track_tags()
            return
        if head == "report":
            self._track_report(args[1:])
            return
        text = " ".join(args).strip()
        if not text:
            console = self.console
            console.print(console.red('usage: jasem track "<what you did>"'))
            console.print(console.dim('  e.g.  jasem track "1h45min debugging the parser, work"'))
            console.print(console.dim("  list entries with ") + console.green("jasem track list")
                          + console.dim(" · review with ") + console.green("jasem track report"))
            return
        self._track_add(text)

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
        when = "today" if entry.date == today.isoformat() else self.calendar.format_iso(entry.date)
        console.print(" ".join([
            console.green(f"✓ tracked #{entry.id}"), console.bold(entry.time_text),
            console.dim("·"), entry.work, console.dim(f"· {when} · #{entry.tag}"),
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
                example = self.calendar.format_iso("2026-07-01")
                console.print(console.red(f"could not understand date: {value!r}"))
                console.print(console.dim(
                    f"  try: today · yesterday · last friday · june 20 · {example}"
                ))
                return None
            entry.date = resolved
            return f"date → {self.calendar.format_iso(resolved)}"
        if field == "tag":
            if value.lower() in CLEAR_WORDS:
                entry.tag = "work"
                return "tag → work"
            entry.tag = value
            return f"tag → {value}"
        entry.work = value
        return f"work → {value}"

    def _track_list(self, args):
        """List logged time entries for a period, optionally filtered by tag.

        Accepts an optional leading period (default ``all``) and trailing tag,
        mirroring ``jasem acc list``.
        """
        entries = self.timelog.load()
        start, end, label, tag_filter = resolve_window(
            [entry.date for entry in entries], args, dt.date.today(), "all"
        )
        selected = [entry for entry in entries if start <= entry.date <= end]
        if tag_filter:
            selected = [entry for entry in selected if entry.tag.lower() == tag_filter]
        header = "Time entries"
        if label != "all time":
            header += "  ·  " + label
        if tag_filter:
            header += "  ·  #" + tag_filter
        self.presenter.time_entries(selected, header)

    def _track_tags(self):
        """Print each category in use across time entries with its count."""
        counts = {}
        for entry in self.timelog.load():
            tag = entry.tag or "work"
            counts[tag] = counts.get(tag, 0) + 1
        console = self.console
        if not counts:
            console.print(console.dim("  (no categories yet)"))
            return
        console.print(console.bold("Categories — time"))
        for tag, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
            console.print(f"  {count:>3}  " + console.cyan("#" + tag))

    def _track_report(self, args):
        """Render an aggregated time report for a period, optionally by tag.

        Accepts an optional leading period (``today``/``week``/``month``/``all``,
        default ``week``) and an optional trailing tag filter.
        """
        entries = self.timelog.load()
        start, end, label, tag_filter = resolve_window(
            [entry.date for entry in entries], args, dt.date.today(), "week"
        )
        selected = [entry for entry in entries if start <= entry.date <= end]
        if tag_filter:
            selected = [entry for entry in selected if entry.tag.lower() == tag_filter]
        report = build_report(selected, start, end, end, label, tag_filter, self.calendar)
        self.presenter.report(report)

    def acc(self, args):
        """Dispatch ``jasem acc`` to recording, listing, editing, or reporting.

        A bare ``rm``/``set``/``list``/``report``/``tags`` first token manages
        existing records or views; any other text is recorded as a new spending
        entry (parsed by AI, with a comma-format fallback when the backend is
        unavailable).
        """
        head = args[0].lower() if args else ""
        if head in ("rm", "remove", "del", "delete"):
            self._acc_remove(args[1:])
            return
        if head in ("set", "edit"):
            self._acc_set(args[1:])
            return
        if head in ("list", "ls"):
            self._acc_list(args[1:])
            return
        if head == "report":
            self._acc_report(args[1:])
            return
        if head == "tags":
            self._acc_tags()
            return
        text = " ".join(args).strip()
        if not text:
            console = self.console
            console.print(console.red('usage: jasem acc "<what you spent on>"'))
            console.print(console.dim('  e.g.  jasem acc "50k lunch with the team, food"'))
            console.print(console.dim("  list records with ") + console.green("jasem acc list")
                          + console.dim(" · review with ") + console.green("jasem acc report"))
            return
        self._acc_add(text)

    def _acc_add(self, text):
        """Parse a free-text record with AI and append it to the spending log.

        Falls back to the ``<amount>, <title>[, <date>][, <tag>]`` comma format
        when the AI backend is unavailable (handled by the parser).
        """
        console = self.console
        today = dt.date.today()
        fields = self.spend_parser.parse(text, today)
        amount = fields.pop("amount")
        record = Spending(**fields)
        records = self.spending.load()
        record.id = self.spending.next_id(records)
        records.append(record)
        self.spending.save(records)
        when = "today" if record.date == today.isoformat() else self.calendar.format_iso(record.date)
        console.print(" ".join([
            console.green(f"✓ recorded #{record.id}"), console.bold(format_amount(record.amount())),
            console.dim("·"), record.title, console.dim(f"· {when} · #{record.tag}"),
        ]))
        if record.description:
            console.print(console.dim("  " + record.description))
        if amount == 0:
            console.warn(console.yellow(
                f"  (couldn't read an amount from {text!r}; "
                "stored as-is, won't count toward totals)"
            ))

    def _acc_remove(self, rest):
        """Delete the spending records whose ids appear in ``rest``."""
        console = self.console
        ids = set()
        for argument in rest:
            try:
                ids.add(int(argument))
            except ValueError:
                pass
        if not ids:
            console.print(console.red("usage: jasem acc rm <id> [id...]"))
            console.print(console.dim(
                '  (to record spending that starts with "rm", quote it: '
                'jasem acc "rm ...")'
            ))
            return
        records = self.spending.load()
        kept = [record for record in records if record.id not in ids]
        removed = len(records) - len(kept)
        self.spending.save(kept)
        console.print(
            console.green(f"✓ removed {removed} spending record(s)")
            if removed else console.red("no matching id(s)")
        )

    def _acc_set(self, args):
        """Update one field of a spending record identified by its id."""
        console = self.console
        if len(args) < 3:
            console.print(console.red(
                "usage: jasem acc set <id> <amount|title|description|date|tag> <value>"))
            console.print(console.dim("  e.g.  jasem acc set 3 amount 60k"))
            console.print(console.dim('        jasem acc set 3 title "dinner out"'))
            console.print(console.dim('        jasem acc set 3 description "team celebration"'))
            console.print(console.dim("        jasem acc set 3 date yesterday"))
            console.print(console.dim("        jasem acc set 3 tag food"))
            return
        try:
            identifier = int(args[0])
        except ValueError:
            console.print(console.red(f"not a valid id: {args[0]}"))
            return
        field = resolve_spend_field(args[1])
        if not field:
            console.print(console.red(f"unknown field: {args[1]}"))
            console.print(console.dim("  fields: amount · title · description · date · tag"))
            return
        records = self.spending.load()
        record = next((item for item in records if item.id == identifier), None)
        if record is None:
            console.print(console.red(f"no spending record with id #{identifier}"))
            return
        message = self._apply_spend_field(record, field, " ".join(args[2:]).strip())
        if message is None:
            return
        self.spending.save(records)
        console.print(console.green(f"✓ #{identifier} updated:") + " " + message)
        console.print(console.dim("  " + record.title))

    def _apply_spend_field(self, record, field, value):
        """Apply ``value`` to ``field`` of ``record``.

        Returns:
            A confirmation message, or ``None`` when the value was rejected
            (an explanation has already been printed).
        """
        console = self.console
        if field == "amount":
            amount = parse_amount(value)
            if amount > 0:
                record.amount_text = format_amount(amount)
                return f"amount → {record.amount_text}"
            record.amount_text = value
            console.warn(console.yellow(
                f"  (couldn't read an amount from {value!r}; "
                "stored as-is, won't count toward totals)"
            ))
            return f"amount → {value}"
        if field == "date":
            resolved = self.dates.resolve(value, dt.date.today())
            if not resolved:
                example = self.calendar.format_iso("2026-07-01")
                console.print(console.red(f"could not understand date: {value!r}"))
                console.print(console.dim(
                    f"  try: today · yesterday · last friday · june 20 · {example}"
                ))
                return None
            record.date = resolved
            return f"date → {self.calendar.format_iso(resolved)}"
        if field == "tag":
            if value.lower() in CLEAR_WORDS:
                record.tag = "general"
                return "tag → general"
            record.tag = value
            return f"tag → {value}"
        if field == "description":
            if value.lower() in CLEAR_WORDS:
                record.description = ""
                return "description cleared"
            record.description = value
            return f"description → {value}"
        record.title = value
        return f"title → {value}"

    def _acc_list(self, args):
        """Render recorded spending for a period, optionally filtered by tag.

        Accepts an optional leading period (default ``all``) and trailing tag,
        mirroring ``jasem track list``.
        """
        records = self.spending.load()
        start, end, label, tag_filter = resolve_window(
            [record.date for record in records], args, dt.date.today(), "all"
        )
        selected = [record for record in records if start <= record.date <= end]
        if tag_filter:
            selected = [record for record in selected if record.tag.lower() == tag_filter]
        header = "Spending"
        if label != "all time":
            header += "  ·  " + label
        if tag_filter:
            header += "  ·  #" + tag_filter
        self.presenter.spending(selected, header)

    def _acc_report(self, args):
        """Render an aggregated spending report for a period, optionally by tag.

        Accepts an optional leading period (``today``/``week``/``month``/``all``,
        default ``week``) and an optional trailing tag filter.
        """
        records = self.spending.load()
        start, end, label, tag_filter = resolve_window(
            [record.date for record in records], args, dt.date.today(), "week"
        )
        selected = [record for record in records if start <= record.date <= end]
        if tag_filter:
            selected = [record for record in selected if record.tag.lower() == tag_filter]
        report = build_spending_report(selected, start, end, end, label, tag_filter, self.calendar)
        self.presenter.spending_report(report)

    def _acc_tags(self):
        """Print each category in use across spending records with its count."""
        counts = {}
        for record in self.spending.load():
            tag = record.tag or "general"
            counts[tag] = counts.get(tag, 0) + 1
        console = self.console
        if not counts:
            console.print(console.dim("  (no categories yet)"))
            return
        console.print(console.bold("Categories — spending"))
        for tag, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
            console.print(f"  {count:>3}  " + console.cyan("#" + tag))
