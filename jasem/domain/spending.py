"""The spending-record domain model."""

from dataclasses import dataclass

from ..shared.amounts import parse_amount


@dataclass
class Spending:
    """A single recorded money-spending entry.

    Attributes:
        id: Stable identifier, assigned by the store; used by
            ``jasem acc rm``/``set`` to address a specific record.
        date: ISO date on which the money was spent.
        amount_text: The amount as a stored string (normalised to a
            ``format_amount`` form when recorded, but any hand-edited number
            :func:`~jasem.shared.amounts.parse_amount` understands is fine).
        text: A short description of what the money was spent on.
        tag: The category for the record.
    """

    id: int = 0
    date: str = ""
    amount_text: str = ""
    text: str = ""
    tag: str = ""

    def amount(self):
        """Return the record's amount as a number (``0.0`` if unparseable)."""
        return parse_amount(self.amount_text)
