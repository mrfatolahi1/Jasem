"""The task domain model."""

from dataclasses import dataclass

PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}
"""Sort weight per priority; lower values sort first."""


@dataclass
class Task:
    """A single to-do item.

    Attributes:
        id: Stable numeric identifier.
        done: Whether the task is complete.
        priority: One of ``high``, ``medium``, or ``low``.
        deadline: ISO date string, or empty when there is no deadline.
        title: Short task description.
        tags: Comma-separated category string.
        created: ISO date on which the task was created.
    """

    id: int = 0
    done: bool = False
    priority: str = "medium"
    deadline: str = ""
    title: str = ""
    tags: str = ""
    created: str = ""

    def tag_list(self):
        """Return the task's tags as a list of lower-cased category names."""
        return [part.strip().lower() for part in self.tags.split(",") if part.strip()]

    def sort_key(self):
        """Return an ordering key: open first, then by deadline, then priority.

        Tasks without a deadline sort after dated ones.
        """
        return (self.done, self.deadline or "9999-99-99", PRIORITY_RANK.get(self.priority, 1))
