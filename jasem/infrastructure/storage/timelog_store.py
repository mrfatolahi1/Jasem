"""Persistence of time-log entries in a Markdown table."""

from ...domain.time_entry import TimeEntry
from .markdown_table import MarkdownTable, sanitize

_COLUMNS = ["ID", "Date", "Time", "Work", "Tag"]
"""Ordered time-log table columns."""

_PREAMBLE = (
    "# Time log\n\n"
    "_Managed by the `jasem track` CLI. Hand-edit rows freely, but keep the column order._\n\n"
)
"""Markdown written above the time-log table."""


class TimeLogStore:
    """Loads and saves :class:`~jasem.domain.time_entry.TimeEntry` objects."""

    def __init__(self, path):
        """Create a store backed by the Markdown file at ``path``."""
        self._table = MarkdownTable(path, _COLUMNS, _PREAMBLE)

    def load(self):
        """Return all stored time entries in file order, skipping bad rows."""
        entries = []
        for cells in self._table.read():
            try:
                identifier = int(cells[0])
            except ValueError:
                continue
            entries.append(TimeEntry(
                id=identifier,
                date=cells[1],
                time_text=cells[2],
                work=cells[3],
                tag=cells[4],
            ))
        return entries

    def save(self, entries):
        """Write ``entries``, replacing the file's contents."""
        rows = [
            [
                str(entry.id),
                entry.date,
                sanitize(entry.time_text),
                sanitize(entry.work),
                sanitize(entry.tag) or "work",
            ]
            for entry in entries
        ]
        self._table.write(rows)

    @staticmethod
    def next_id(entries):
        """Return the next free identifier given the current ``entries``."""
        return max((entry.id for entry in entries), default=0) + 1
