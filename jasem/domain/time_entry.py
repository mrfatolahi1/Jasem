"""The time-log entry domain model."""

from dataclasses import dataclass

from ..durations import parse_minutes


@dataclass
class TimeEntry:
    """A single tracked block of time.

    Attributes:
        date: ISO date on which the work happened.
        time_text: The duration exactly as the user typed it.
        work: A short description of what was worked on.
        tag: The category for the entry.
    """

    date: str
    time_text: str
    work: str
    tag: str

    def minutes(self):
        """Return the entry's duration in whole minutes (``0`` if unparseable)."""
        return parse_minutes(self.time_text)
