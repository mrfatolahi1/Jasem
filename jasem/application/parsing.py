"""Turning free-text descriptions into structured task and time-log fields."""

import datetime as dt
import urllib.error

from ..domain.task import PRIORITY_RANK
from ..infrastructure.providers.base import TASK_SCHEMA, TIME_ENTRY_SCHEMA
from ..shared.durations import format_minutes, parse_minutes

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
            fields = provider.parse(self._build_prompt(text, today), TASK_SCHEMA)
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


_TRACK_RULES = (
    "Extract a single time-tracking entry from the text below.\n"
    "- minutes: the total duration in WHOLE minutes (1h45min -> 105, 2h -> 120, "
    "half an hour -> 30, an hour and a half -> 90); 0 if no duration is stated.\n"
    "- work: short description of what was worked on, WITHOUT the duration, date, "
    "or tag words.\n"
    "- date_phrase: the exact temporal words as written, for example "
    "yesterday / monday / june 18; empty string if none.\n"
    "- date: your best YYYY-MM-DD guess for when the work happened, empty string "
    "if none.\n"
    "- tag: one short category word such as work, personal, finance; empty string "
    "if none.\n"
)
"""Field-extraction instructions sent to the model for ``jasem track``."""

_TRACK_EXAMPLES = (
    'Example. Text: "2h coding the API yesterday, work" -> '
    '{"minutes": 120, "work": "coding the API", "date_phrase": "yesterday", '
    '"date": "", "tag": "work"}\n'
    'Example. Text: "spent an hour and 45 min on the parser" -> '
    '{"minutes": 105, "work": "on the parser", "date_phrase": "", '
    '"date": "", "tag": ""}\n'
)
"""Few-shot examples appended to the tracking prompt."""


class TimeEntryParser:
    """Produces structured time-log fields, falling back to comma parsing on error.

    Mirrors :class:`TaskParser`: the model turns free text into a duration, a
    work description, a date, and a tag, and an unreachable or misconfigured
    backend degrades to the original ``<time>, <work>[, <date>][, <tag>]``
    comma format instead of failing.
    """

    def __init__(self, provider_factory, config, date_resolver, console):
        """Wire the parser to its collaborators.

        Args:
            provider_factory: Callable taking the config and returning an
                :class:`~jasem.infrastructure.providers.base.AIProvider`.
            config: The resolved :class:`~jasem.shared.config.Config`.
            date_resolver: Resolver turning phrases into ISO dates.
            console: Console used to report backend failures.
        """
        self._provider_factory = provider_factory
        self.config = config
        self.dates = date_resolver
        self.console = console

    def parse(self, text, today=None):
        """Return time-log fields for ``text``.

        Attempts AI extraction first and falls back to comma parsing when the
        backend is unreachable or returns something unusable. The result
        contains ``date``, ``time_text``, ``work``, ``tag``, and ``minutes``;
        ``time_text`` is normalised to a canonical ``"1h 45min"`` form so the
        stored duration always totals back to ``minutes``.

        Args:
            text: The user's free-text tracking description.
            today: Reference date; defaults to today.

        Returns:
            A dict ready to build a
            :class:`~jasem.domain.time_entry.TimeEntry` (plus ``minutes``).
        """
        today = today or dt.date.today()
        try:
            provider = self._provider_factory(self.config)
            fields = provider.parse(self._build_prompt(text, today), TIME_ENTRY_SCHEMA)
            minutes = self._coerce_minutes(fields.get("minutes"))
            work = (fields.get("work") or text).strip()
            date_value = self.dates.resolve(
                fields.get("date_phrase", ""), today, fields.get("date", "")
            )
            if not date_value:
                date_value = self.dates.resolve(text, today)
            tag = str(fields.get("tag", "") or "").strip()
        except (urllib.error.URLError, urllib.error.HTTPError) as error:
            self.console.warn(self.console.red(
                f"! Couldn't parse with the {self.config.provider} backend ({error}); "
                "tracked with plain parsing."
            ))
            minutes, work, date_value, tag = self._local_fallback(text, today)
        except Exception as error:
            self.console.warn(self.console.red(f"! Parse error ({error}); tracked raw text."))
            minutes, work, date_value, tag = self._local_fallback(text, today)
        return {
            "date": date_value or today.isoformat(),
            "time_text": format_minutes(minutes) if minutes > 0 else text.strip(),
            "work": work,
            "tag": tag or "work",
            "minutes": minutes,
        }

    def _local_fallback(self, text, today):
        """Parse the legacy ``<time>, <work>[, <date>][, <tag>]`` form locally.

        Returns:
            A ``(minutes, work, date, tag)`` tuple. With no comma, the whole
            text is treated as the work and scanned for a duration.
        """
        parts = [part.strip() for part in text.split(",") if part.strip()]
        if len(parts) >= 2:
            time_text, work, extra = parts[0], parts[1], parts[2:]
        else:
            time_text, work, extra = text.strip(), text.strip(), []
        date_value, tag = "", ""
        for item in extra:
            resolved = self.dates.resolve(item, today)
            if resolved and not date_value:
                date_value = resolved
            elif not tag:
                tag = item
        return parse_minutes(time_text), work, date_value, tag

    @staticmethod
    def _coerce_minutes(value):
        """Return ``value`` as a non-negative int, or ``0`` when not a number."""
        try:
            return max(0, int(round(float(value))))
        except (TypeError, ValueError):
            return 0

    def _build_prompt(self, text, today):
        """Assemble the tracking prompt for ``text`` relative to ``today``."""
        return (
            f"Today is {today.isoformat()} ({today.strftime('%A')}).\n"
            f"{_TRACK_RULES}\n{_TRACK_EXAMPLES}\nText: {text}"
        )
