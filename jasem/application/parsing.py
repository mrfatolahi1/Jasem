"""Turning free-text task descriptions into structured fields."""

import datetime as dt
import urllib.error

from ..domain.task import PRIORITY_RANK

_RULES = (
    "Extract structured fields from the task description below.\n"
    "- title: short imperative summary, WITHOUT any date/priority/tag words.\n"
    "- deadline_phrase: the exact temporal words as written, for example "
    "next thursday / tomorrow / june 20 / in 3 days; empty string if none.\n"
    "- deadline_date: your best YYYY-MM-DD guess for the deadline, empty string if none.\n"
    "- priority: low, medium, or high (default medium).\n"
    "- tags: short topic words mentioned such as work, finance, personal; "
    "empty list if none.\n"
    "Always capture any time words (tomorrow, friday, next week, by june 20) "
    "in deadline_phrase, even when they follow words like 'by' or 'due'.\n"
)
"""Field-extraction instructions sent to the model."""

_EXAMPLES = (
    'Example. Task: "review Ali PR by tomorrow, work" -> '
    '{"title": "review Ali PR", "deadline_phrase": "tomorrow", '
    '"deadline_date": "", "priority": "medium", "tags": ["work"]}\n'
    'Example. Task: "pay rent next friday high priority" -> '
    '{"title": "pay rent", "deadline_phrase": "next friday", '
    '"deadline_date": "", "priority": "high", "tags": []}\n'
)
"""Few-shot examples appended to the prompt."""


class TaskParser:
    """Produces structured task fields, falling back to local parsing on error.

    The AI provider is created lazily per parse so that an unreachable or
    misconfigured backend degrades to regex date parsing instead of aborting
    commands that never need a model.
    """

    def __init__(self, provider_factory, config, date_resolver, console):
        """Wire the parser to its collaborators.

        Args:
            provider_factory: Callable taking the config and returning an
                :class:`~jasem.providers.base.AIProvider`.
            config: The resolved :class:`~jasem.config.Config`.
            date_resolver: Resolver turning phrases into ISO dates.
            console: Console used to report backend failures.
        """
        self._provider_factory = provider_factory
        self.config = config
        self.dates = date_resolver
        self.console = console

    def parse(self, text, today=None):
        """Return task fields for ``text``.

        Attempts AI extraction first and falls back to regex date parsing when
        the backend is unreachable or returns something unusable. The result
        always contains ``done``, ``priority``, ``deadline``, ``title``,
        ``tags``, and ``created``.

        Args:
            text: The user's task description.
            today: Reference date; defaults to today.

        Returns:
            A dict of task fields suitable for constructing a
            :class:`~jasem.domain.task.Task`.
        """
        today = today or dt.date.today()
        try:
            provider = self._provider_factory(self.config)
            fields = provider.parse(self._build_prompt(text, today))
            title = (fields.get("title") or text).strip()
            deadline = self.dates.resolve(
                fields.get("deadline_phrase", ""), today, fields.get("deadline_date", "")
            )
            if not deadline:
                deadline = self.dates.resolve(text, today)
            priority = fields.get("priority", "medium")
            if priority not in PRIORITY_RANK:
                priority = "medium"
            tags = [str(tag).strip() for tag in fields.get("tags", []) if str(tag).strip()]
        except (urllib.error.URLError, urllib.error.HTTPError) as error:
            self.console.warn(self.console.red(
                f"! Couldn't parse with the {self.config.provider} backend ({error}); "
                "saved without AI parsing."
            ))
            title, deadline, priority, tags = self._local_fallback(text, today)
        except Exception as error:
            self.console.warn(self.console.red(f"! Parse error ({error}); storing raw text."))
            title, deadline, priority, tags = self._local_fallback(text, today)
        return {
            "done": False,
            "priority": priority,
            "deadline": deadline,
            "title": title,
            "tags": ", ".join(tags),
            "created": today.isoformat(),
        }

    def _local_fallback(self, text, today):
        """Return fields parsed without a model: raw title and regex date."""
        return text.strip(), self.dates.resolve(text, today), "medium", []

    def _build_prompt(self, text, today):
        """Assemble the extraction prompt for ``text`` relative to ``today``."""
        return (
            f"Today is {today.isoformat()} ({today.strftime('%A')}).\n"
            f"{_RULES}\n{_EXAMPLES}\nTask: {text}"
        )
