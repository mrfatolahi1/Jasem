"""Local Ollama provider."""

import json

from .base import TASK_SCHEMA, AIProvider
from .http import request_json


class OllamaProvider(AIProvider):
    """Parses tasks with a locally running Ollama model."""

    def parse(self, prompt):
        """Send ``prompt`` to Ollama's chat endpoint with a schema constraint.

        Returns:
            The decoded task fields.
        """
        payload = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "format": TASK_SCHEMA,
            "options": {"temperature": 0},
        }
        response = request_json(self.config.ollama_host + "/api/chat", payload, {})
        return json.loads(response["message"]["content"])
