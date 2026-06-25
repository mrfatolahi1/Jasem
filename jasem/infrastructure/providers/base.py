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
"""JSON schema describing the fields ``jasem add`` extracts."""

TIME_ENTRY_SCHEMA = {
    "type": "object",
    "properties": {
        "minutes": {"type": "integer"},
        "work": {"type": "string"},
        "date_phrase": {"type": "string"},
        "date": {"type": "string"},
        "tag": {"type": "string"},
    },
    "required": ["minutes", "work", "date_phrase", "date", "tag"],
}
"""JSON schema describing the fields ``jasem track`` extracts."""

SPENDING_SCHEMA = {
    "type": "object",
    "properties": {
        "amount": {"type": "number"},
        "title": {"type": "string"},
        "date_phrase": {"type": "string"},
        "date": {"type": "string"},
        "tag": {"type": "string"},
    },
    "required": ["amount", "title", "date_phrase", "date", "tag"],
}
"""JSON schema describing the fields ``jasem acc`` extracts."""


class AIProvider(ABC):
    """Abstract base for backends that extract structured fields from free text."""

    def __init__(self, config):
        """Store the configuration the provider needs.

        Args:
            config: The resolved :class:`~jasem.config.Config`.
        """
        self.config = config

    @abstractmethod
    def parse(self, prompt, schema=TASK_SCHEMA):
        """Return the structured fields described by ``schema`` for ``prompt``.

        Args:
            prompt: The fully built extraction prompt.
            schema: JSON schema the reply must match; defaults to
                :data:`TASK_SCHEMA` for backward compatibility.

        Returns:
            A mapping matching ``schema``.
        """
