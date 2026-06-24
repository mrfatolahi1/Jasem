"""Rendering of tasks and time-log entries for the terminal."""

from ..shared.charts import BAR_WIDTH, bar
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
                identifier = console.cyan(("#" + str(entry.id)).rjust(4))
                console.print(f"    {identifier}  {entry.time_text.rjust(9)}   {entry.work}  {tag}")
        if len(by_date) > 1:
            console.print(
                "\n  " + console.dim("total ") + console.bold(format_minutes(grand_total))
            )

    def report(self, report):
        """Print an aggregated time :class:`~jasem.application.reports.Report`.

        Renders a title, a summary stats block, and three bar-chart sections
        (by tag, a daily/weekly timeline, and top activities).

        Args:
            report: The aggregated figures to display.
        """
        console = self.console
        title = f"Time report — {report.label} ({report.start} → {report.end})"
        if report.tag_filter:
            title += "  ·  #" + report.tag_filter
        console.print(console.bold(title))
        if report.entry_count == 0:
            console.print(console.dim("  (nothing tracked)"))
            return
        self._report_summary(report)
        self._report_by_tag(report)
        self._report_timeline(report)
        self._report_activities(report)

    def _bar(self, value, max_value, style="cyan"):
        """Return a colored bar padded with spaces to a fixed width.

        Padding keeps the value column that follows the bar aligned across rows.
        """
        raw = bar(value, max_value)
        return self.console.style(style, raw) + " " * (BAR_WIDTH - len(raw))

    def _report_summary(self, report):
        """Print the headline numbers: total, entries, active days, averages."""
        console = self.console

        def stat(label, value):
            return "  " + console.dim(label.ljust(15)) + console.bold(value)

        console.print("")
        console.print(stat("total", format_minutes(report.total_minutes)))
        console.print(stat("entries", str(report.entry_count)))
        console.print(stat("active days", f"{report.active_days} of {report.span_days}"))
        console.print(stat("avg active day", format_minutes(report.avg_per_active_day)))
        if report.busiest_day:
            date, minutes = report.busiest_day
            console.print(stat("busiest day", f"{date}  ({format_minutes(minutes)})"))

    def _report_by_tag(self, report):
        """Print a horizontal bar chart of time per tag, with percentages."""
        if not report.by_tag:
            return
        console = self.console
        console.print("\n  " + console.bold(console.cyan("By tag")))
        max_minutes = max(minutes for _, minutes in report.by_tag)
        width = max(len(tag) for tag, _ in report.by_tag) + 1
        for tag, minutes in report.by_tag:
            pct = round(minutes / report.total_minutes * 100) if report.total_minutes else 0
            label = console.cyan(("#" + tag).ljust(width))
            console.print(
                f"    {label}  {self._bar(minutes, max_minutes, 'cyan')}  "
                + console.bold(format_minutes(minutes).rjust(9))
                + console.dim(f"  {pct:>3}%")
            )

    def _report_timeline(self, report):
        """Print a per-day (or per-week) bar chart across the whole period."""
        if not report.timeline:
            return
        console = self.console
        heading = "Weekly timeline" if report.timeline_unit == "week" else "Daily timeline"
        console.print("\n  " + console.bold(console.cyan(heading)))
        max_minutes = max((minutes for _, minutes in report.timeline), default=0)
        width = max(len(label) for label, _ in report.timeline)
        for label, minutes in report.timeline:
            value = console.bold(format_minutes(minutes)) if minutes else console.dim("·")
            console.print(
                f"    {console.cyan(label.ljust(width))}  "
                + self._bar(minutes, max_minutes, "green") + "  " + value
            )

    def _report_activities(self, report):
        """Print a ranked bar chart of the most time-consuming activities."""
        if not report.top_activities:
            return
        console = self.console
        console.print("\n  " + console.bold(console.cyan("Top activities")))
        max_minutes = max(minutes for _, minutes, _ in report.top_activities)
        width = min(max(len(work) for work, _, _ in report.top_activities), 28)
        for work, minutes, count in report.top_activities:
            name = work if len(work) <= width else work[: width - 1] + "…"
            tally = console.dim(f"  ×{count}") if count > 1 else ""
            console.print(
                f"    {name.ljust(width)}  {self._bar(minutes, max_minutes, 'cyan')}  "
                + console.bold(format_minutes(minutes).rjust(9)) + tally
            )
