"""Tests for the OpenAI-compatible provider."""

import unittest
from unittest import mock

from jasem.config import Config
from jasem.providers import openai as openai_module
from jasem.providers.openai import OpenAIProvider


class OpenAIProviderTests(unittest.TestCase):
    """Verify the provider targets the OpenAI-specific base URL."""

    def test_uses_openai_specific_base(self):
        """The request goes to the OpenAI base, not the shared Anthropic one."""
        config = Config({
            "JASEM_API_BASE": "https://anthropic-proxy.example",
            "JASEM_OPENAI_API_BASE": "https://openai-proxy.example/v1",
        })
        provider = OpenAIProvider(config)
        calls = []

        def fake_request_json(url, payload, headers, timeout=120):
            """Record the URL and return a minimal valid completion."""
            calls.append(url)
            return {"choices": [{"message": {"content": "{}"}}]}

        with mock.patch.object(openai_module, "request_json", fake_request_json):
            self.assertEqual(provider.parse("parse this"), {})
        self.assertEqual(calls[0], "https://openai-proxy.example/v1/chat/completions")

    def test_defaults_to_public_openai(self):
        """With no base configured the public OpenAI endpoint is used."""
        provider = OpenAIProvider(Config({}))
        self.assertEqual(provider.base_url(), "https://api.openai.com/v1")


if __name__ == "__main__":
    unittest.main()
