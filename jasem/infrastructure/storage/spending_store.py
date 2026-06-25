"""Persistence of spending records in a Markdown table."""

from ...domain.spending import Spending
from .markdown_table import MarkdownTable, sanitize

_COLUMNS = ["ID", "Date", "Amount", "Title", "Tag"]
"""Ordered spending-log table columns."""

_PREAMBLE = (
    "# Spending log\n\n"
    "_Managed by the `jasem acc` CLI. Hand-edit rows freely, but keep the column order._\n\n"
)
"""Markdown written above the spending table."""


class SpendingStore:
    """Loads and saves :class:`~jasem.domain.spending.Spending` objects."""

    def __init__(self, path):
        """Create a store backed by the Markdown file at ``path``."""
        self._table = MarkdownTable(path, _COLUMNS, _PREAMBLE)

    def load(self):
        """Return all stored spending records in file order, skipping bad rows."""
        records = []
        for cells in self._table.read():
            try:
                identifier = int(cells[0])
            except ValueError:
                continue
            records.append(Spending(
                id=identifier,
                date=cells[1],
                amount_text=cells[2],
                title=cells[3],
                tag=cells[4],
            ))
        return records

    def save(self, records):
        """Write ``records``, replacing the file's contents."""
        rows = [
            [
                str(record.id),
                record.date,
                sanitize(record.amount_text),
                sanitize(record.title),
                sanitize(record.tag) or "general",
            ]
            for record in records
        ]
        self._table.write(rows)

    @staticmethod
    def next_id(records):
        """Return the next free identifier given the current ``records``."""
        return max((record.id for record in records), default=0) + 1
