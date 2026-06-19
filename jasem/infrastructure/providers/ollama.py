"""Local Ollama provider."""

import json

from .base import TASK_SCHEMA, AIProvider
from .http import request_json


class OllamaProvider(AIProvider):
    """Parses tasks with a locally running Ollama model."""

    def parse(self, prompt, schema=TASK_SCHEMA):
        """Send ``prompt`` to Ollama's chat endpoint with a schema constraint.

        Returns:
            The decoded fields matching ``schema``.
        """
        payload = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "format": schema,
            "options": {"temperature": 0},
        }
        response = request_json(self.config.ollama_host + "/api/chat", payload, {})
        return json.loads(response["message"]["content"])
