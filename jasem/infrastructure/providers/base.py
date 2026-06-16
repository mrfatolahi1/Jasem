"""Provider interface and the structured schema jasem extracts."""

from abc import ABC, abstractmethod

TASK_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "deadline_phrase": {"type": "string"},
        "deadline_date": {"type": "string"},
        "priority": {"type": "string", "enum": ["low", "medium", "high"]},
        "tags": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["title", "deadline_phrase", "deadline_date", "priority", "tags"],
}
"""JSON schema describing the fields every provider must return."""


class AIProvider(ABC):
    """Abstract base for backends that extract task fields from free text."""

    def __init__(self, config):
        """Store the configuration the provider needs.

        Args:
            config: The resolved :class:`~jasem.config.Config`.
        """
        self.config = config

    @abstractmethod
    def parse(self, prompt):
        """Return the structured task fields for ``prompt``.

        Args:
            prompt: The fully built extraction prompt.

        Returns:
            A mapping matching :data:`TASK_SCHEMA`.
        """
