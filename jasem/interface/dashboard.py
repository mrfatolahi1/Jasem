"""The at-a-glance home screen shown when ``jasem`` is run with no arguments.

Reads the three logs and renders a single, offline screen: the tasks that need
attention now (overdue, due today, then soonest), plus today's tracked time and
spending with a seven-day activity sparkline. No AI backend or network is
touched, so it stays instant.
"""

import datetime as dt

from ..shared.amounts import format_amount
from ..shared.charts import sparkline
from ..shared.durations import format_minutes
from .layout import rule


class Dashboard:
    """Renders the no-args summary from already-loaded log data."""

    FOCUS_LIMIT = 7
    """Most tasks the focus list shows before it stops, to keep the screen short."""

    def __init__(self, console, calendar, presenter):
        """Bind to the shared console, calendar view, and task presenter."""
        self.console = console
        self.calendar = calendar
        self.presenter = presenter

    def render(self, tasks, entries, records, today_date):
        """Print the dashboard for ``today_date`` from the loaded logs.

        Args:
            tasks: All stored tasks.
            entries: All stored time entries.
            records: All stored spending records.
            today_date: Today's :class:`datetime.date`.
        """
        console = self.console
        today = today_date.isoformat()
        greeting = f"{today_date.strftime('%A')} · {self.calendar.format_iso(today)}"
        console.print(rule(console, title="jasem", summary=greeting))
        console.print("")
        self._focus_section(tasks, today)
        console.print("")
        self._activity(entries, records, today_date)
        console.print("")
        console.print(self._hint())

    def _focus_section(self, tasks, today):
        """Print the tasks needing attention now, with a full-set footer summary."""
        console = self.console
        open_tasks = [task for task in tasks if not task.done]
        console.print(rule(console, "Focus"))
        if not open_tasks:
            console.print(console.dim("   inbox zero — nothing open; add one with ")
                          + console.green('jasem todo "…"'))
            return
        focus = self._focus(open_tasks, today)
        for line in self.presenter.task_lines(focus, today):
            console.print(line)
        summary = self.presenter.task_summary(open_tasks, today)
        hidden = len(open_tasks) - len(focus)
        if hidden > 0:
            summary += f"  ·  +{hidden} more"
        console.print(rule(console, summary=summary))

    def _focus(self, open_tasks, today):
        """Return the open tasks that matter now: overdue, due today, then soonest."""
        ordered = sorted(open_tasks, key=lambda task: task.sort_key())
        overdue = [task for task in ordered if task.deadline and task.deadline < today]
        due_today = [task for task in ordered if task.deadline == today]
        chosen = list(overdue) + [task for task in due_today if task not in overdue]
        for task in ordered:
            if len(chosen) >= self.FOCUS_LIMIT:
                break
            if task not in chosen:
                chosen.append(task)
        return chosen[: self.FOCUS_LIMIT]

    def _activity(self, entries, records, today_date):
        """Print today's tracked time and spending with a seven-day sparkline."""
        console = self.console
        today = today_date.isoformat()
        tracked = sum(entry.minutes() for entry in entries if entry.date == today)
        spent = sum(record.amount() for record in records if record.date == today)
        week = [(today_date - dt.timedelta(days=offset)).isoformat()
                for offset in range(6, -1, -1)]
        series = [sum(entry.minutes() for entry in entries if entry.date == day)
                  for day in week]
        spark = sparkline(series)

        console.print("  " + console.bold(console.accent("Today")))
        trend = ("   " + console.accent(spark) + console.dim("  last 7 days")) if spark else ""
        console.print("   " + console.dim("tracked".ljust(9))
                      + console.bold(format_minutes(tracked)) + trend)
        console.print("   " + console.dim("spent".ljust(9))
                      + console.bold(format_amount(spent)))

    def _hint(self):
        """Return the dim footer pointing at the three namespaces and help."""
        console = self.console
        commands = console.dim(" · ").join(
            console.green(name) for name in ("jasem todo", "jasem track", "jasem acc"))
        return "  " + commands + console.dim("    ·    ") + console.green("jasem help")
