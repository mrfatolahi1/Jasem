"""Rendering of tasks, time-log entries, and spending for the terminal."""

from ..shared.amounts import format_amount
from ..shared.calendar_view import CalendarView
from ..shared.charts import BAR_WIDTH, bar, sparkline
from ..shared.durations import format_minutes
from ..shared.relative_dates import age, relative_day
from .layout import Column, Table, rule


class Presenter:
    """Formats domain objects into styled console output."""

    def __init__(self, console, calendar=None):
        """Bind the presenter to a :class:`~jasem.console.Console` and calendar view."""
        self.console = console
        self.calendar = calendar or CalendarView(False)

    # -- tasks ---------------------------------------------------------------

    def tasks(self, tasks, header, today):
        """Print ``tasks`` under ``header``, sorted, colored, and width-aware.

        Args:
            tasks: The tasks to display.
            header: Section title.
            today: ISO date used to flag overdue and due-today items.
        """
        console = self.console
        items = sorted(tasks, key=lambda item: item.sort_key())
        console.print(rule(console, header))
        if not items:
            console.print(console.dim("   nothing here — add one: ")
                          + console.green('jasem todo "…"'))
            return
        for line in self.task_lines(items, today):
            console.print(line)
        console.print(rule(console, summary=self.task_summary(items, today)))

    def task_lines(self, items, today):
        """Return ``items`` rendered as task table rows, preserving their order.

        Shared by the list views and the dashboard so a subset of tasks can be
        shown with a footer summarising the full set.
        """
        table = Table(self.console, [
            Column(),                                          # status glyph
            Column(align="right", style=self.console.accent),  # id
            Column(),                                           # priority badge
            Column(),                                           # due
            Column(flex=True, min_width=12, max_width=46),     # title
            Column(style=self.console.dim),                    # tags
            Column(align="right", style=self.console.dim),     # age
        ])
        return table.render([self._task_row(task, today) for task in items])

    def _task_row(self, task, today):
        """Return one task as a list of table cells."""
        console = self.console
        status = ("✓", console.green) if task.done else ("●", console.accent)
        priority = self._priority_cell(task)
        due = self._due_cell(task, today)
        title = (task.title, console.dim) if task.done else (task.title, None)
        tags = "#" + task.tags.replace(", ", " #") if task.tags else ""
        created = age(task.created, today) if task.created else ""
        return [status, str(task.id), priority, due, title, tags, created]

    def _priority_cell(self, task):
        """Return the styled priority badge cell for ``task``."""
        console = self.console
        label = {"high": "⚑ high", "medium": "  med", "low": "  low"}.get(
            task.priority, "  " + task.priority)
        if task.done:
            return (label, console.dim)
        if task.priority == "high":
            return (label, lambda text: console.bold(console.red(text)))
        if task.priority == "low":
            return (label, console.dim)
        return (label, None)

    def _due_cell(self, task, today):
        """Return the styled deadline cell, relative for near dates, dim otherwise."""
        console = self.console
        if not task.deadline:
            return ("—", console.dim)
        relative = relative_day(task.deadline, today)
        if task.done:
            return (self.calendar.format_iso(task.deadline), console.dim)
        if relative == "overdue":
            return ("overdue", console.red)
        if relative == "today":
            return ("today", lambda text: console.bold(console.yellow(text)))
        if relative == "tomorrow":
            return ("tomorrow", console.yellow)
        if relative.startswith("in ") and relative.endswith("d"):
            return (relative, None)
        return (self.calendar.format_iso(task.deadline), console.dim)

    def task_summary(self, items, today):
        """Return the footer summary line for a task list."""
        open_tasks = [task for task in items if not task.done]
        due_today = sum(1 for task in open_tasks if task.deadline == today)
        overdue = sum(1 for task in open_tasks
                      if task.deadline and task.deadline < today)
        parts = [f"{len(open_tasks)} open" if open_tasks else f"{len(items)} done"]
        if due_today:
            parts.append(f"{due_today} due today")
        if overdue:
            parts.append(f"{overdue} overdue")
        return "  ·  ".join(parts)

    # -- time entries --------------------------------------------------------

    def time_entries(self, entries, header):
        """Print time-log ``entries`` under ``header``, oldest first.

        Args:
            entries: The time entries to display.
            header: Section title.
        """
        console = self.console
        items = sorted(entries, key=lambda item: (item.date, item.id))
        console.print(rule(console, header))
        if not items:
            console.print(console.dim("   nothing here — log time: ")
                          + console.green('jasem track "…"'))
            return
        table = Table(console, [
            Column(align="right", style=console.accent),       # id
            Column(style=console.dim),                         # date
            Column(align="right", style=console.bold),         # duration
            Column(flex=True, min_width=12, max_width=48),     # work
            Column(style=console.dim),                         # tag
        ])
        rows = [[
            str(entry.id),
            self.calendar.format_iso(entry.date) or "—",
            entry.time_text,
            entry.work,
            "#" + entry.tag if entry.tag else "",
        ] for entry in items]
        for line in table.render(rows):
            console.print(line)
        total = sum(entry.minutes() for entry in items)
        console.print(rule(console, summary=f"{format_minutes(total)} · {len(items)} entries"))

    # -- spending ------------------------------------------------------------

    def spending(self, records, header):
        """Print spending ``records`` under ``header``, oldest first.

        Args:
            records: The spending records to display.
            header: Section title.
        """
        console = self.console
        items = sorted(records, key=lambda item: (item.date, item.id))
        console.print(rule(console, header))
        if not items:
            console.print(console.dim("   nothing here — record one: ")
                          + console.green('jasem acc "…"'))
            return
        table = Table(console, [
            Column(align="right", style=console.accent),       # id
            Column(style=console.dim),                         # date
            Column(align="right", style=console.bold),         # amount
            Column(flex=True, min_width=12, max_width=48),     # title
            Column(style=console.dim),                         # tag
        ])
        rows = [[
            str(record.id),
            self.calendar.format_iso(record.date) or "—",
            format_amount(record.amount()),
            record.title,
            "#" + record.tag if record.tag else "",
        ] for record in items]
        lines = table.render(rows)
        for record, line in zip(items, lines):
            console.print(line)
            if record.description:
                console.print(console.dim("       ↳ " + record.description))
        total = sum(record.amount() for record in items)
        console.print(rule(console, summary=f"{format_amount(total)} · {len(items)} records"))

    # -- shared report helpers ----------------------------------------------

    def _bar(self, value, max_value, style="cyan"):
        """Return a colored bar padded with spaces to a fixed width.

        Padding keeps the value column that follows the bar aligned across rows.
        """
        raw = bar(value, max_value)
        return self.console.style(style, raw) + " " * (BAR_WIDTH - len(raw))

    def _trend(self, total, previous, higher_is_good):
        """Return a styled period-over-period trend cell, or ``None`` when unknown."""
        if not previous:
            return None
        console = self.console
        delta = total - previous
        pct = round(delta / previous * 100)
        arrow = "▲" if delta > 0 else ("▼" if delta < 0 else "■")
        good = (delta > 0) == higher_is_good
        style = console.green if delta and good else (console.red if delta else console.dim)
        sign = "+" if delta > 0 else ""
        return style(f"{arrow} {sign}{pct}%")

    # -- time report ---------------------------------------------------------

    def report(self, report):
        """Print an aggregated time :class:`~jasem.application.reports.Report`."""
        console = self.console
        start = self.calendar.format_iso(report.start)
        end = self.calendar.format_iso(report.end)
        title = f"Time report — {report.label} ({start} → {end})"
        if report.tag_filter:
            title += "  ·  #" + report.tag_filter
        console.print(rule(console, title))
        if report.entry_count == 0:
            console.print(console.dim("   (nothing tracked)"))
            return
        self._report_summary(report)
        self._report_by_tag(report)
        self._report_timeline(report)
        self._report_activities(report)
        console.print("")
        console.print(rule(console, summary=(
            f"total {format_minutes(report.total_minutes)} · {report.entry_count} entries")))

    def _report_summary(self, report):
        """Print the headline numbers: total, entries, active days, averages."""
        console = self.console

        def stat(label, value):
            return "  " + console.dim(label.ljust(15)) + value

        console.print("")
        console.print(stat("total", console.bold(format_minutes(report.total_minutes))))
        console.print(stat("entries", console.bold(str(report.entry_count))))
        console.print(stat("active days", console.bold(
            f"{report.active_days} of {report.span_days}")))
        console.print(stat("avg active day", console.bold(
            format_minutes(report.avg_per_active_day))))
        if report.busiest_day:
            date, minutes = report.busiest_day
            shown = self.calendar.format_iso(date)
            console.print(stat("busiest day", console.bold(
                f"{shown}  ({format_minutes(minutes)})")))
        trend = self._trend(report.total_minutes, getattr(report, "previous_total", 0), True)
        if trend:
            console.print(stat("vs previous", trend))
        spark = sparkline([minutes for _, minutes in report.timeline])
        if spark:
            console.print(stat("trend", console.accent(spark)))

    def _report_by_tag(self, report):
        """Print a horizontal bar chart of time per tag, with percentages."""
        if not report.by_tag:
            return
        console = self.console
        console.print("\n  " + console.bold(console.accent("By tag")))
        max_minutes = max(minutes for _, minutes in report.by_tag)
        width = max(len(tag) for tag, _ in report.by_tag) + 1
        for tag, minutes in report.by_tag:
            pct = round(minutes / report.total_minutes * 100) if report.total_minutes else 0
            label = console.accent(("#" + tag).ljust(width))
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
        console.print("\n  " + console.bold(console.accent(heading)))
        max_minutes = max((minutes for _, minutes in report.timeline), default=0)
        width = max(len(label) for label, _ in report.timeline)
        for label, minutes in report.timeline:
            value = console.bold(format_minutes(minutes)) if minutes else console.dim("·")
            console.print(
                f"    {console.accent(label.ljust(width))}  "
                + self._bar(minutes, max_minutes, "green") + "  " + value
            )

    def _report_activities(self, report):
        """Print a ranked bar chart of the most time-consuming activities."""
        if not report.top_activities:
            return
        console = self.console
        console.print("\n  " + console.bold(console.accent("Top activities")))
        max_minutes = max(minutes for _, minutes, _ in report.top_activities)
        width = min(max(len(work) for work, _, _ in report.top_activities), 28)
        for work, minutes, count in report.top_activities:
            name = work if len(work) <= width else work[: width - 1] + "…"
            tally = console.dim(f"  ×{count}") if count > 1 else ""
            console.print(
                f"    {name.ljust(width)}  {self._bar(minutes, max_minutes, 'cyan')}  "
                + console.bold(format_minutes(minutes).rjust(9)) + tally
            )

    # -- spending report -----------------------------------------------------

    def spending_report(self, report):
        """Print an aggregated spending
        :class:`~jasem.application.reports.SpendingReport`.
        """
        console = self.console
        start = self.calendar.format_iso(report.start)
        end = self.calendar.format_iso(report.end)
        title = f"Spending report — {report.label} ({start} → {end})"
        if report.tag_filter:
            title += "  ·  #" + report.tag_filter
        console.print(rule(console, title))
        if report.record_count == 0:
            console.print(console.dim("   (nothing recorded)"))
            return
        self._spending_summary(report)
        self._spending_by_tag(report)
        self._spending_timeline(report)
        self._spending_top(report)
        console.print("")
        console.print(rule(console, summary=(
            f"total {format_amount(report.total_amount)} · {report.record_count} records")))

    def _spending_summary(self, report):
        """Print the headline numbers: total, records, active days, averages."""
        console = self.console

        def stat(label, value):
            return "  " + console.dim(label.ljust(15)) + value

        console.print("")
        console.print(stat("total", console.bold(format_amount(report.total_amount))))
        console.print(stat("records", console.bold(str(report.record_count))))
        console.print(stat("active days", console.bold(
            f"{report.active_days} of {report.span_days}")))
        console.print(stat("avg active day", console.bold(
            format_amount(report.avg_per_active_day))))
        if report.biggest_day:
            date, amount = report.biggest_day
            shown = self.calendar.format_iso(date)
            console.print(stat("biggest day", console.bold(
                f"{shown}  ({format_amount(amount)})")))
        trend = self._trend(report.total_amount, getattr(report, "previous_total", 0), False)
        if trend:
            console.print(stat("vs previous", trend))
        spark = sparkline([amount for _, amount in report.timeline])
        if spark:
            console.print(stat("trend", console.accent(spark)))

    def _spending_by_tag(self, report):
        """Print a horizontal bar chart of spending per tag, with percentages."""
        if not report.by_tag:
            return
        console = self.console
        console.print("\n  " + console.bold(console.accent("By tag")))
        max_amount = max(amount for _, amount in report.by_tag)
        width = max(len(tag) for tag, _ in report.by_tag) + 1
        for tag, amount in report.by_tag:
            pct = round(amount / report.total_amount * 100) if report.total_amount else 0
            label = console.accent(("#" + tag).ljust(width))
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
        console.print("\n  " + console.bold(console.accent(heading)))
        max_amount = max((amount for _, amount in report.timeline), default=0)
        width = max(len(label) for label, _ in report.timeline)
        for label, amount in report.timeline:
            value = console.bold(format_amount(amount)) if amount else console.dim("·")
            console.print(
                f"    {console.accent(label.ljust(width))}  "
                + self._bar(amount, max_amount, "green") + "  " + value
            )

    def _spending_top(self, report):
        """Print a ranked bar chart of the biggest spends."""
        if not report.top_spends:
            return
        console = self.console
        console.print("\n  " + console.bold(console.accent("Top spends")))
        max_amount = max(amount for _, amount, _ in report.top_spends)
        width = min(max(len(text) for text, _, _ in report.top_spends), 28)
        for text, amount, count in report.top_spends:
            name = text if len(text) <= width else text[: width - 1] + "…"
            tally = console.dim(f"  ×{count}") if count > 1 else ""
            console.print(
                f"    {name.ljust(width)}  {self._bar(amount, max_amount, 'cyan')}  "
                + console.bold(format_amount(amount).rjust(12)) + tally
            )
