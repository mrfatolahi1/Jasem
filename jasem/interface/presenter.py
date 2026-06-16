"""Rendering of tasks and time-log entries for the terminal."""

from ..shared.durations import format_minutes


class Presenter:
    """Formats domain objects into styled console output."""

    def __init__(self, console):
        """Bind the presenter to a :class:`~jasem.console.Console`."""
        self.console = console

    def tasks(self, tasks, header, today):
        """Print ``tasks`` under ``header``, sorted and colored by status.

        Args:
            tasks: The tasks to display.
            header: Section title.
            today: ISO date used to flag overdue and due-today items.
        """
        console = self.console
        if not tasks:
            console.print(console.dim("  (nothing here)"))
            return
        console.print(console.bold(header))
        for task in sorted(tasks, key=lambda item: item.sort_key()):
            console.print("  " + self._task_line(task, today))

    def _task_line(self, task, today):
        """Return a single formatted, colored task row."""
        console = self.console
        mark = console.green("☑") if task.done else "☐"
        deadline = task.deadline or "—"
        if not task.done and task.deadline:
            if task.deadline < today:
                deadline = console.red(deadline + " (overdue)")
            elif task.deadline == today:
                deadline = console.yellow(deadline + " (today)")
        priority = task.priority
        if priority == "high":
            priority = console.bold(console.red(priority))
        elif priority == "low":
            priority = console.dim(priority)
        tags = console.dim("#" + task.tags.replace(", ", " #")) if task.tags else ""
        title = console.dim(task.title) if task.done else task.title
        identifier = console.cyan(str(task.id).rjust(3))
        return f"{mark} {identifier}  [{priority}]  {deadline}  {title}  {tags}"

    def timelog(self, entries, header, today):
        """Print ``entries`` grouped by date with per-day and grand totals.

        Args:
            entries: The time entries to display.
            header: Section title.
            today: ISO date used to label the current day.
        """
        console = self.console
        if not entries:
            console.print(console.bold(header))
            console.print(console.dim("  (nothing tracked)"))
            return
        by_date = {}
        for entry in entries:
            by_date.setdefault(entry.date, []).append(entry)
        grand_total = 0
        console.print(console.bold(header))
        for date in sorted(by_date, reverse=True):
            day_entries = by_date[date]
            day_total = sum(entry.minutes() for entry in day_entries)
            grand_total += day_total
            label = date + (" (today)" if date == today else "")
            console.print(
                "\n  " + console.bold(console.cyan(label))
                + console.dim("  —  ") + console.bold(format_minutes(day_total))
            )
            for entry in day_entries:
                tag = console.dim("#" + entry.tag) if entry.tag else ""
                console.print(f"    {entry.time_text.rjust(9)}   {entry.work}  {tag}")
        if len(by_date) > 1:
            console.print(
                "\n  " + console.dim("total ") + console.bold(format_minutes(grand_total))
            )
