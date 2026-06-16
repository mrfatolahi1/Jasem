"""Anthropic (Claude) provider."""

from .base import TASK_SCHEMA, AIProvider
from .http import request_json


class AnthropicProvider(AIProvider):
    """Parses tasks with Anthropic's Messages API using forced tool use."""

    def base_url(self):
        """Return the configured Anthropic base URL, or the public default."""
        return self.config.api_base or "https://api.anthropic.com"

    def parse(self, prompt):
        """Call the Messages API and read the forced ``tool_use`` input.

        Returns:
            The decoded task fields.

        Raises:
            ValueError: If the response contains no ``tool_use`` block.
        """
        headers = {"x-api-key": self.config.api_key, "anthropic-version": "2023-06-01"}
        body = {
            "model": self.config.model,
            "max_tokens": 1024,
            "tools": [{
                "name": "record_task",
                "description": "Record the structured fields extracted from the task.",
                "input_schema": TASK_SCHEMA,
            }],
            "tool_choice": {"type": "tool", "name": "record_task"},
            "messages": [{"role": "user", "content": prompt}],
        }
        response = request_json(self.base_url() + "/v1/messages", body, headers)
        for block in response.get("content", []):
            if block.get("type") == "tool_use":
                return block.get("input", {})
        raise ValueError("Anthropic response contained no tool_use block")
