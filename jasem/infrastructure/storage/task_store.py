"""Persistence of tasks in a Markdown table."""

from ...domain.task import Task
from .markdown_table import MarkdownTable, sanitize

_COLUMNS = ["ID", "✓", "Priority", "Deadline", "Task", "Tags", "Created"]
"""Ordered task table columns."""

_PREAMBLE = (
    "# Tasks\n\n"
    "_Managed by the `jasem` CLI. You can hand-edit rows, but keep the column order._\n\n"
)
"""Markdown written above the task table."""


class TaskStore:
    """Loads and saves :class:`~jasem.domain.task.Task` objects on disk."""

    def __init__(self, path):
        """Create a store backed by the Markdown file at ``path``."""
        self._table = MarkdownTable(path, _COLUMNS, _PREAMBLE)

    def load(self):
        """Return all stored tasks in file order, skipping unparseable rows."""
        tasks = []
        for cells in self._table.read():
            try:
                identifier = int(cells[0])
            except ValueError:
                continue
            tasks.append(Task(
                id=identifier,
                done=cells[1] == "☑",
                priority=cells[2] or "medium",
                deadline="" if cells[3] == "-" else cells[3],
                title=cells[4],
                tags="" if cells[5] == "-" else cells[5],
                created=cells[6],
            ))
        return tasks

    def save(self, tasks):
        """Write ``tasks``, replacing the file's contents."""
        rows = [
            [
                str(task.id),
                "☑" if task.done else "☐",
                task.priority,
                task.deadline or "-",
                sanitize(task.title),
                sanitize(task.tags) or "-",
                task.created,
            ]
            for task in tasks
        ]
        self._table.write(rows)

    @staticmethod
    def next_id(tasks):
        """Return the next free identifier given the current ``tasks``."""
        return max((task.id for task in tasks), default=0) + 1
