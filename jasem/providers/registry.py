"""Selection of an AI provider by configured name."""

from .anthropic import AnthropicProvider
from .ollama import OllamaProvider
from .openai import OpenAIProvider

_PROVIDERS = {
    "ollama": OllamaProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
}
"""Maps provider names to their implementation classes."""


def get_provider(config):
    """Return a provider instance for ``config.provider``.

    Args:
        config: The resolved :class:`~jasem.config.Config`.

    Returns:
        An :class:`~jasem.providers.base.AIProvider` instance.

    Raises:
        ValueError: If the configured provider name is unknown.
    """
    try:
        provider_class = _PROVIDERS[config.provider]
    except KeyError:
        raise ValueError(
            f"unknown JASEM_PROVIDER={config.provider!r}; use ollama, openai, or anthropic"
        )
    return provider_class(config)
