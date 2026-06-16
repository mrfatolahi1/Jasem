"""OpenAI-compatible provider."""

import urllib.error

from .base import AIProvider
from .http import extract_json, request_json

_SYSTEM_PROMPT = (
    "You output only a single JSON object with the requested fields. "
    "No prose, no markdown, no code fences."
)
"""System message instructing the model to return bare JSON."""


class OpenAIProvider(AIProvider):
    """Parses tasks with any OpenAI-compatible chat completions endpoint."""

    def base_url(self):
        """Return the configured OpenAI base URL, or the public default."""
        return self.config.openai_api_base or "https://api.openai.com/v1"

    def parse(self, prompt):
        """Call the chat completions endpoint and decode the JSON reply.

        Sends ``response_format=json_object`` and retries once without it when
        the endpoint rejects that field with a 400, since not every compatible
        server supports it.

        Returns:
            The decoded task fields.
        """
        headers = {}
        if self.config.api_key:
            headers["Authorization"] = "Bearer " + self.config.api_key
        body = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        url = self.base_url() + "/chat/completions"
        try:
            response = request_json(url, body, headers)
        except urllib.error.HTTPError as error:
            if error.code != 400:
                raise
            body.pop("response_format", None)
            response = request_json(url, body, headers)
        return extract_json(response["choices"][0]["message"]["content"])
