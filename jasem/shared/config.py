"""Environment-driven configuration for jasem.

Every ``JASEM_*`` and provider-specific environment variable is read in one
place so the rest of the package depends on a plain :class:`Config` object
rather than reading ``os.environ`` directly.
"""

import os

DEFAULT_MODELS = {
    "ollama": "qwen2.5:3b",
    "openai": "gpt-4o-mini",
    "anthropic": "claude-opus-4-8",
}

FALLBACK_MODEL = "qwen2.5:3b"


def clean_base_url(value):
    """
    Normalise a base URL by trimming whitespace and any trailing slash.
    """
    return (value or "").strip().rstrip("/")


class Config:
    """Resolved snapshot of jasem's runtime settings.

    The configuration is read once from an environment mapping and then handed
    to the storage, provider, parsing, and application layers.
    """

    def __init__(self, env=None):
        """Resolve settings from an environment mapping.

        Args:
            env: Mapping of environment variables. Defaults to ``os.environ``.
        """
        env = os.environ if env is None else env
        self.provider = env.get("JASEM_PROVIDER", "ollama").strip().lower()
        self.ollama_host = (env.get("OLLAMA_HOST") or "http://localhost:11434").rstrip(
            "/"
        )
        self.api_base = clean_base_url(env.get("JASEM_API_BASE"))
        self.openai_api_base = (
            clean_base_url(env.get("JASEM_OPENAI_API_BASE"))
            or clean_base_url(env.get("JASEM_OPENAI_BASE_URL"))
            or clean_base_url(env.get("OPENAI_BASE_URL"))
            or self.api_base
        )
        self.api_key = (
            env.get("JASEM_API_KEY")
            or env.get("OPENAI_API_KEY")
            or env.get("ANTHROPIC_API_KEY")
            or ""
        )
        self.model = env.get("JASEM_MODEL") or DEFAULT_MODELS.get(
            self.provider, FALLBACK_MODEL
        )
        self.directory = os.path.expanduser(env.get("JASEM_DIR", "~/.jasem"))
        self.task_file = os.path.expanduser(
            env.get("JASEM_FILE", os.path.join(self.directory, "tasks.md"))
        )
        self.track_file = os.path.expanduser(
            env.get("JASEM_TRACK_FILE", os.path.join(self.directory, "timelog.md"))
        )
