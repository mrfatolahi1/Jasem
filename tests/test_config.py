"""Tests for environment-driven configuration."""

import unittest

from jasem.shared.config import Config


class ConfigBaseUrlTests(unittest.TestCase):
    """Verify the OpenAI base-URL precedence chain."""

    def test_openai_base_prefers_provider_specific_env(self):
        """The jasem-specific variable wins over the standard and shared ones."""
        config = Config({
            "JASEM_API_BASE": "https://shared.example/v1",
            "OPENAI_BASE_URL": "https://openai-env.example/v1",
            "JASEM_OPENAI_API_BASE": "https://openai-specific.example/v1/",
        })
        self.assertEqual(config.api_base, "https://shared.example/v1")
        self.assertEqual(config.openai_api_base, "https://openai-specific.example/v1")

    def test_openai_base_accepts_standard_env_name(self):
        """The standard ``OPENAI_BASE_URL`` is honored and trailing-slash trimmed."""
        config = Config({"OPENAI_BASE_URL": "https://compatible.example/api/v1/"})
        self.assertEqual(config.openai_api_base, "https://compatible.example/api/v1")

    def test_openai_base_falls_back_to_shared(self):
        """With only the shared base set, OpenAI reuses it (backward compatible)."""
        config = Config({"JASEM_API_BASE": "https://shared.example/v1"})
        self.assertEqual(config.openai_api_base, "https://shared.example/v1")

    def test_defaults_when_environment_empty(self):
        """An empty environment yields the documented defaults."""
        config = Config({})
        self.assertEqual(config.provider, "ollama")
        self.assertEqual(config.model, "qwen2.5:3b")
        self.assertEqual(config.openai_api_base, "")
        self.assertFalse(config.jalali)


class JalaliFlagTests(unittest.TestCase):
    """The JASEM_JALALI flag is read as a boolean."""

    def test_truthy_values_enable(self):
        """The accepted truthy spellings all turn Jalali mode on."""
        for value in ("1", "true", "TRUE", "yes", "on", " True "):
            self.assertTrue(Config({"JASEM_JALALI": value}).jalali, value)

    def test_other_values_disable(self):
        """Anything else (including unset) leaves Jalali mode off."""
        for value in ("0", "false", "no", "off", ""):
            self.assertFalse(Config({"JASEM_JALALI": value}).jalali, value)


if __name__ == "__main__":
    unittest.main()
