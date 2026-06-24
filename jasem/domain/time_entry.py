"""The time-log entry domain model."""

from dataclasses import dataclass

from ..shared.durations import parse_minutes


@dataclass
class TimeEntry:
    """A single tracked block of time.

    Attributes:
        id: Stable identifier, assigned by the store; used by
            ``jasem track rm``/``set`` to address a specific entry.
        date: ISO date on which the work happened.
        time_text: The duration as a human-readable string (normalised to a
            ``"1h 45min"`` form when logged, but any hand-edited spelling that
            :func:`~jasem.shared.durations.parse_minutes` understands is fine).
        work: A short description of what was worked on.
        tag: The category for the entry.
    """

    id: int = 0
    date: str = ""
    time_text: str = ""
    work: str = ""
    tag: str = ""

    def minutes(self):
        """Return the entry's duration in whole minutes (``0`` if unparseable)."""
        return parse_minutes(self.time_text)
