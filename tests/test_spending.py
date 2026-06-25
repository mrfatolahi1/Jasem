"""Tests for AI-backed spending records and amount parsing."""

import datetime as dt
import io
import os
import shutil
import tempfile
import unittest
import urllib.error

from jasem.application.app import App
from jasem.application.parsing import SpendingParser
from jasem.domain.spending import Spending
from jasem.infrastructure.providers.base import SPENDING_SCHEMA
from jasem.shared.amounts import format_amount, parse_amount
from jasem.shared.config import Config
from jasem.shared.console import Console
from jasem.shared.dates import DateResolver

TODAY = dt.date(2026, 6, 19)


class RecordingConsole(Console):
    """Console that writes nowhere and remembers the warnings it was given."""

    def __init__(self):
        """Bind to a throwaway buffer (color off) and start an empty log."""
        super().__init__(io.StringIO())
        self.warnings = []

    def warn(self, text):
        """Capture a warning instead of writing to stderr."""
        self.warnings.append(text)


class FakeProvider:
    """Stand-in provider returning canned fields or raising a set error."""

    def __init__(self, fields=None, error=None):
        """Configure the reply ``fields`` or the ``error`` to raise."""
        self._fields = fields or {}
        self._error = error
        self.calls = []

    def parse(self, prompt, schema=None):
        """Record the call, then raise the configured error or return fields."""
        self.calls.append((prompt, schema))
        if self._error:
            raise self._error
        return self._fields


def make_parser(provider, env=None):
    """Return a :class:`SpendingParser` wired to ``provider``."""
    return SpendingParser(
        lambda config: provider, Config(env or {}), DateResolver(), RecordingConsole()
    )


class AmountParsingTests(unittest.TestCase):
    """The amount helpers read shorthand and render with separators."""

    def test_parse_plain_number(self):
        """A bare number is read as-is."""
        self.assertEqual(parse_amount("50000"), 50000.0)

    def test_parse_k_suffix(self):
        """``50k`` scales by a thousand."""
        self.assertEqual(parse_amount("50k"), 50000.0)

    def test_parse_m_suffix_with_decimal(self):
        """``1.5m`` scales by a million."""
        self.assertEqual(parse_amount("1.5m"), 1500000.0)

    def test_parse_thousands_commas(self):
        """Commas are treated as thousands separators."""
        self.assertEqual(parse_amount("1,200"), 1200.0)

    def test_parse_number_embedded_in_text(self):
        """The first number anywhere in the text is used."""
        self.assertEqual(parse_amount("paid 50k"), 50000.0)

    def test_parse_unparseable_is_zero(self):
        """Text with no number yields zero."""
        self.assertEqual(parse_amount("nothing here"), 0.0)

    def test_format_whole_number(self):
        """Whole amounts get thousands separators and no decimals."""
        self.assertEqual(format_amount(50000), "50,000")

    def test_format_large_number(self):
        """Millions are grouped too."""
        self.assertEqual(format_amount(1500000), "1,500,000")

    def test_format_strips_trailing_zeros(self):
        """A fractional amount drops trailing zeros."""
        self.assertEqual(format_amount(1500.5), "1,500.5")


class SpendingParserTests(unittest.TestCase):
    """The AI path builds normalised records and degrades gracefully."""

    def test_normalises_amount_and_applies_defaults(self):
        """Amount becomes a canonical ``amount_text`` and blanks get defaults."""
        provider = FakeProvider(
            {"amount": 50000, "text": "lunch with the team",
             "date_phrase": "", "date": "", "tag": ""}
        )
        fields = make_parser(provider).parse("50k lunch with the team", TODAY)
        self.assertEqual(fields["amount"], 50000)
        self.assertEqual(fields["amount_text"], "50,000")
        self.assertEqual(fields["text"], "lunch with the team")
        self.assertEqual(fields["tag"], "general")
        self.assertEqual(fields["date"], "2026-06-19")
        self.assertEqual(provider.calls[0][1], SPENDING_SCHEMA)

    def test_resolves_relative_date_phrase(self):
        """A ``date_phrase`` is resolved relative to today."""
        provider = FakeProvider(
            {"amount": 30000, "text": "snacks", "date_phrase": "yesterday",
             "date": "", "tag": "food"}
        )
        fields = make_parser(provider).parse("30k snacks yesterday", TODAY)
        self.assertEqual(fields["date"], "2026-06-18")

    def test_coerces_string_amount(self):
        """An amount returned as a string is still understood."""
        provider = FakeProvider(
            {"amount": "1500000", "text": "phone", "date_phrase": "", "date": "", "tag": ""}
        )
        fields = make_parser(provider).parse("1.5m phone", TODAY)
        self.assertEqual(fields["amount"], 1500000)
        self.assertEqual(fields["amount_text"], "1,500,000")

    def test_zero_amount_keeps_raw_text(self):
        """With no amount the original text is stored as-is for visibility."""
        provider = FakeProvider(
            {"amount": 0, "text": "groceries", "date_phrase": "", "date": "", "tag": ""}
        )
        fields = make_parser(provider).parse("bought some groceries", TODAY)
        self.assertEqual(fields["amount"], 0)
        self.assertEqual(fields["amount_text"], "bought some groceries")

    def test_falls_back_to_comma_format_when_backend_down(self):
        """A network error degrades to comma parsing and warns."""
        provider = FakeProvider(error=urllib.error.URLError("offline"))
        console = RecordingConsole()
        parser = SpendingParser(lambda config: provider, Config({}), DateResolver(), console)
        fields = parser.parse("50k, lunch, yesterday, food", TODAY)
        self.assertEqual(fields["amount"], 50000)
        self.assertEqual(fields["amount_text"], "50,000")
        self.assertEqual(fields["text"], "lunch")
        self.assertEqual(fields["date"], "2026-06-18")
        self.assertEqual(fields["tag"], "food")
        self.assertTrue(console.warnings)


class AccCommandTests(unittest.TestCase):
    """End-to-end ``jasem acc`` add path against a temporary spending file."""

    def setUp(self):
        """Create a temp directory and config pointing the spend file at it."""
        self.tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmpdir)
        self.config = Config({
            "JASEM_SPEND_FILE": os.path.join(self.tmpdir, "spending.md"),
            "JASEM_FILE": os.path.join(self.tmpdir, "tasks.md"),
        })

    def test_acc_writes_normalised_record(self):
        """A free-text record is parsed, normalised, and persisted."""
        app = App(self.config, RecordingConsole())
        provider = FakeProvider(
            {"amount": 50000, "text": "lunch", "date_phrase": "today",
             "date": "", "tag": "food"}
        )
        app.spend_parser._provider_factory = lambda config: provider
        app.run(["acc", "50k lunch today"])
        records = app.spending.load()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].amount_text, "50,000")
        self.assertEqual(records[0].amount(), 50000)
        self.assertEqual(records[0].text, "lunch")
        self.assertEqual(records[0].id, 1)


class AccManageTests(unittest.TestCase):
    """Editing and removing existing spending records via ``jasem acc``."""

    def setUp(self):
        """Create a temp spend file and an app sharing one recording console."""
        self.tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmpdir)
        self.config = Config({
            "JASEM_SPEND_FILE": os.path.join(self.tmpdir, "spending.md"),
            "JASEM_FILE": os.path.join(self.tmpdir, "tasks.md"),
        })
        self.console = RecordingConsole()
        self.app = App(self.config, self.console)

    def _seed(self):
        """Persist two known records with ids 1 and 2."""
        self.app.spending.save([
            Spending(id=1, date="2026-06-19", amount_text="50,000", text="lunch", tag="food"),
            Spending(id=2, date="2026-06-18", amount_text="20,000", text="taxi", tag="transport"),
        ])

    def _record(self, identifier):
        """Return the reloaded record with ``identifier``."""
        return next(r for r in self.app.spending.load() if r.id == identifier)

    def test_add_assigns_incrementing_ids(self):
        """Successive recorded entries receive 1, 2, … via ``next_id``."""
        provider = FakeProvider(
            {"amount": 10000, "text": "a", "date_phrase": "today", "date": "", "tag": "food"}
        )
        self.app.spend_parser._provider_factory = lambda config: provider
        self.app.run(["acc", "10k a today"])
        self.app.run(["acc", "10k a today"])
        self.assertEqual([r.id for r in self.app.spending.load()], [1, 2])

    def test_rm_removes_record(self):
        """``acc rm`` drops the matching id and keeps the rest."""
        self._seed()
        self.app.run(["acc", "rm", "1"])
        self.assertEqual([r.id for r in self.app.spending.load()], [2])

    def test_rm_unknown_id_keeps_everything(self):
        """An id that matches nothing leaves the log untouched."""
        self._seed()
        self.app.run(["acc", "rm", "99"])
        self.assertEqual(len(self.app.spending.load()), 2)

    def test_set_text(self):
        """``acc set <id> text …`` joins the remaining words."""
        self._seed()
        self.app.run(["acc", "set", "1", "text", "dinner", "out"])
        self.assertEqual(self._record(1).text, "dinner out")

    def test_set_amount_normalises(self):
        """A parseable amount is stored in canonical form."""
        self._seed()
        self.app.run(["acc", "set", "2", "amount", "1.5m"])
        self.assertEqual(self._record(2).amount_text, "1,500,000")

    def test_set_amount_unparseable_warns_and_stores_raw(self):
        """An unreadable amount is kept as-is and a warning is emitted."""
        self._seed()
        self.app.run(["acc", "set", "2", "amount", "lots"])
        self.assertEqual(self._record(2).amount_text, "lots")
        self.assertTrue(self.console.warnings)

    def test_set_date_resolves(self):
        """An ISO date is accepted for the date field."""
        self._seed()
        self.app.run(["acc", "set", "1", "date", "2026-07-01"])
        self.assertEqual(self._record(1).date, "2026-07-01")

    def test_set_tag(self):
        """The tag field takes a single category."""
        self._seed()
        self.app.run(["acc", "set", "1", "tag", "groceries"])
        self.assertEqual(self._record(1).tag, "groceries")


class JalaliAccTests(unittest.TestCase):
    """Jalali mode shows Persian dates while storing Gregorian on disk."""

    def setUp(self):
        """An app with JASEM_JALALI on, writing to a temp spend file."""
        self.tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmpdir)
        self.config = Config({
            "JASEM_SPEND_FILE": os.path.join(self.tmpdir, "spending.md"),
            "JASEM_FILE": os.path.join(self.tmpdir, "tasks.md"),
            "JASEM_JALALI": "true",
        })
        self.console = RecordingConsole()
        self.app = App(self.config, self.console)

    def _output(self):
        """Return everything printed to the console buffer so far."""
        return self.console.stream.getvalue()

    def test_jalali_input_stored_gregorian_shown_jalali(self):
        """A typed Jalali date is stored Gregorian and echoed back in Jalali."""
        provider = FakeProvider(
            {"amount": 30000, "text": "snacks", "date_phrase": "1404-04-04",
             "date": "", "tag": "food"}
        )
        self.app.spend_parser._provider_factory = lambda config: provider
        self.app.run(["acc", "30k snacks 1404-04-04"])
        record = self.app.spending.load()[0]
        self.assertEqual(record.date, "2025-06-25")
        self.assertIn("1404-04-04", self._output())
        self.assertNotIn("2025-06-25", self._output())

    def test_set_date_accepts_jalali_input(self):
        """``acc set <id> date`` reads a Jalali date and stores Gregorian."""
        self.app.spending.save([
            Spending(id=1, date="2026-06-19", amount_text="10,000", text="x", tag="food"),
        ])
        self.app.run(["acc", "set", "1", "date", "1405-04-04"])
        record = next(r for r in self.app.spending.load() if r.id == 1)
        self.assertEqual(record.date, "2026-06-25")
        self.assertIn("1405-04-04", self._output())


if __name__ == "__main__":
    unittest.main()
