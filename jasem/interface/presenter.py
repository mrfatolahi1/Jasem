"""Rendering of tasks and time-log entries for the terminal."""

from ..shared.amounts import format_amount
from ..shared.calendar_view import CalendarView
from ..shared.charts import BAR_WIDTH, bar
from ..shared.durations import format_minutes


class Presenter:
    """Formats domain objects into styled console output."""

    def __init__(self, console, calendar=None):
        """Bind the presenter to a :class:`~jasem.console.Console` and calendar view."""
        self.console = console
        self.calendar = calendar or CalendarView(False)

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
        deadline = self.calendar.format_iso(task.deadline) or "—"
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

    def time_entries(self, entries, header):
        """Print time-log ``entries`` under ``header``, oldest first.

        Args:
            entries: The time entries to display.
            header: Section title.
        """
        console = self.console
        if not entries:
            console.print(console.dim("  (nothing here)"))
            return
        console.print(console.bold(header))
        for entry in sorted(entries, key=lambda item: (item.date, item.id)):
            console.print("  " + self._time_entry_line(entry))

    def _time_entry_line(self, entry):
        """Return a single formatted, colored time-entry row."""
        console = self.console
        identifier = console.cyan(str(entry.id).rjust(3))
        date = self.calendar.format_iso(entry.date) or "—"
        duration = console.bold(entry.time_text.rjust(8))
        tag = console.dim("#" + entry.tag) if entry.tag else ""
        return f"{identifier}  {date}  {duration}  {entry.work}  {tag}"

    def report(self, report):
        """Print an aggregated time :class:`~jasem.application.reports.Report`.

        Renders a title, a summary stats block, and three bar-chart sections
        (by tag, a daily/weekly timeline, and top activities).

        Args:
            report: The aggregated figures to display.
        """
        console = self.console
        start = self.calendar.format_iso(report.start)
        end = self.calendar.format_iso(report.end)
        title = f"Time report — {report.label} ({start} → {end})"
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
            shown = self.calendar.format_iso(date)
            console.print(stat("busiest day", f"{shown}  ({format_minutes(minutes)})"))

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

    def spending(self, records, header):
        """Print spending ``records`` under ``header``, oldest first.

        Args:
            records: The spending records to display.
            header: Section title.
        """
        console = self.console
        if not records:
            console.print(console.dim("  (nothing here)"))
            return
        console.print(console.bold(header))
        for record in sorted(records, key=lambda item: (item.date, item.id)):
            console.print("  " + self._spending_line(record))

    def _spending_line(self, record):
        """Return a single formatted, colored spending row."""
        console = self.console
        identifier = console.cyan(str(record.id).rjust(3))
        date = self.calendar.format_iso(record.date) or "—"
        amount = console.bold(format_amount(record.amount()).rjust(12))
        tag = console.dim("#" + record.tag) if record.tag else ""
        note = console.dim("— " + record.description) if record.description else ""
        return f"{identifier}  {date}  {amount}  {record.title}  {note}  {tag}"

    def spending_report(self, report):
        """Print an aggregated spending
        :class:`~jasem.application.reports.SpendingReport`.

        Renders a title, a summary stats block, and three bar-chart sections
        (by tag, a daily/weekly timeline, and top spends).

        Args:
            report: The aggregated figures to display.
        """
        console = self.console
        start = self.calendar.format_iso(report.start)
        end = self.calendar.format_iso(report.end)
        title = f"Spending report — {report.label} ({start} → {end})"
        if report.tag_filter:
            title += "  ·  #" + report.tag_filter
        console.print(console.bold(title))
        if report.record_count == 0:
            console.print(console.dim("  (nothing recorded)"))
            return
        self._spending_summary(report)
        self._spending_by_tag(report)
        self._spending_timeline(report)
        self._spending_top(report)

    def _spending_summary(self, report):
        """Print the headline numbers: total, records, active days, averages."""
        console = self.console

        def stat(label, value):
            return "  " + console.dim(label.ljust(15)) + console.bold(value)

        console.print("")
        console.print(stat("total", format_amount(report.total_amount)))
        console.print(stat("records", str(report.record_count)))
        console.print(stat("active days", f"{report.active_days} of {report.span_days}"))
        console.print(stat("avg active day", format_amount(report.avg_per_active_day)))
        if report.biggest_day:
            date, amount = report.biggest_day
            shown = self.calendar.format_iso(date)
            console.print(stat("biggest day", f"{shown}  ({format_amount(amount)})"))

    def _spending_by_tag(self, report):
        """Print a horizontal bar chart of spending per tag, with percentages."""
        if not report.by_tag:
            return
        console = self.console
        console.print("\n  " + console.bold(console.cyan("By tag")))
        max_amount = max(amount for _, amount in report.by_tag)
        width = max(len(tag) for tag, _ in report.by_tag) + 1
        for tag, amount in report.by_tag:
            pct = round(amount / report.total_amount * 100) if report.total_amount else 0
            label = console.cyan(("#" + tag).ljust(width))
            console.print(
                f"    {label}  {self._bar(amount, max_amount, 'cyan')}  "
                + console.bold(format_amount(amount).rjust(12))
                + console.dim(f"  {pct:>3}%")
            )

    def _spending_timeline(self, report):
        """Print a per-day (or per-week) bar chart across the whole period."""
        if not report.timeline:
            return
        console = self.console
        heading = "Weekly timeline" if report.timeline_unit == "week" else "Daily timeline"
        console.print("\n  " + console.bold(console.cyan(heading)))
        max_amount = max((amount for _, amount in report.timeline), default=0)
        width = max(len(label) for label, _ in report.timeline)
        for label, amount in report.timeline:
            value = console.bold(format_amount(amount)) if amount else console.dim("·")
            console.print(
                f"    {console.cyan(label.ljust(width))}  "
                + self._bar(amount, max_amount, "green") + "  " + value
            )

    def _spending_top(self, report):
        """Print a ranked bar chart of the biggest spends."""
        if not report.top_spends:
            return
        console = self.console
        console.print("\n  " + console.bold(console.cyan("Top spends")))
        max_amount = max(amount for _, amount, _ in report.top_spends)
        width = min(max(len(text) for text, _, _ in report.top_spends), 28)
        for text, amount, count in report.top_spends:
            name = text if len(text) <= width else text[: width - 1] + "…"
            tally = console.dim(f"  ×{count}") if count > 1 else ""
            console.print(
                f"    {name.ljust(width)}  {self._bar(amount, max_amount, 'cyan')}  "
                + console.bold(format_amount(amount).rjust(12)) + tally
            )
