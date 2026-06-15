import importlib
import os
import unittest
from unittest import mock

import jasem


class OpenAIBaseUrlTests(unittest.TestCase):
    def reload_jasem(self, env):
        with mock.patch.dict(os.environ, env, clear=True):
            module = importlib.reload(jasem)
        self.addCleanup(importlib.reload, jasem)
        return module

    def test_openai_base_prefers_provider_specific_env(self):
        module = self.reload_jasem({
            "JASEM_API_BASE": "https://shared.example/v1",
            "OPENAI_BASE_URL": "https://openai-env.example/v1",
            "JASEM_OPENAI_API_BASE": "https://openai-specific.example/v1/",
        })

        self.assertEqual(module.API_BASE, "https://shared.example/v1")
        self.assertEqual(module.OPENAI_API_BASE, "https://openai-specific.example/v1")

    def test_openai_base_accepts_standard_env_name(self):
        module = self.reload_jasem({
            "OPENAI_BASE_URL": "https://compatible.example/api/v1/",
        })

        self.assertEqual(module.OPENAI_API_BASE, "https://compatible.example/api/v1")

    def test_openai_parser_uses_openai_specific_base(self):
        module = self.reload_jasem({
            "JASEM_API_BASE": "https://anthropic-proxy.example",
            "JASEM_OPENAI_API_BASE": "https://openai-proxy.example/v1",
        })
        calls = []

        def fake_http_json(url, payload, headers, timeout=120):
            calls.append((url, payload, headers, timeout))
            return {"choices": [{"message": {"content": "{}"}}]}

        module._http_json = fake_http_json

        self.assertEqual(module._parse_openai("parse this"), {})
        self.assertEqual(
            calls[0][0],
            "https://openai-proxy.example/v1/chat/completions",
        )


if __name__ == "__main__":
    unittest.main()
