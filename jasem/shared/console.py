"""Terminal output styling.

:class:`Console` applies ANSI color codes only when standard output is an
interactive terminal, so redirected or piped output stays plain text. The
``NO_COLOR`` and ``FORCE_COLOR`` environment variables override that detection,
following the conventions at https://no-color.org and https://force-color.org.
"""

import os
import re
import shutil
import sys

ANSI_CODES = {
    "red": "31",
    "yellow": "33",
    "green": "32",
    "blue": "34",
    "magenta": "35",
    "cyan": "36",
    "white": "37",
    "dim": "2",
    "bold": "1",
    "italic": "3",
    "underline": "4",
}

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
"""Matches an SGR escape sequence, so styled text can be measured and padded."""


class Console:
    """Writes styled text to an output stream, coloring only a real terminal."""

    def __init__(self, stream=None, accent="cyan", env=None):
        """Bind the console to a stream and detect terminal support.

        Args:
            stream: Output stream. Defaults to ``sys.stdout``.
            accent: The themable highlight color — an :data:`ANSI_CODES` name or
                an ``"r,g,b"`` truecolor triple.
            env: Environment mapping consulted for ``NO_COLOR``/``FORCE_COLOR``.
                Defaults to ``os.environ``.
        """
        env = os.environ if env is None else env
        self.stream = stream if stream is not None else sys.stdout
        self.accent_name = (accent or "cyan").strip().lower()
        is_tty = bool(getattr(self.stream, "isatty", lambda: False)())
        forced = (env.get("FORCE_COLOR") or "").strip()
        if "NO_COLOR" in env:
            self.color = False
        elif forced and forced != "0":
            self.color = True
        else:
            self.color = is_tty

    def style(self, name, text):
        """Return ``text`` wrapped in the named ANSI style.

        Args:
            name: Style name present in :data:`ANSI_CODES`.
            text: Text to style.

        Returns:
            Styled text when color is enabled, otherwise ``text`` unchanged.
        """
        if not self.color:
            return text
        return f"\033[{ANSI_CODES[name]}m{text}\033[0m"

    def rgb(self, text, red, green, blue):
        """Return ``text`` painted with a 24-bit truecolor foreground."""
        if not self.color:
            return text
        return f"\033[38;2;{red};{green};{blue}m{text}\033[0m"

    def accent(self, text):
        """Return ``text`` in the configured accent color (default cyan).

        The accent may be a style name (``cyan``, ``magenta`` …) or an
        ``"r,g,b"`` truecolor triple; an unrecognised value falls back to cyan.
        """
        name = self.accent_name
        if "," in name:
            try:
                red, green, blue = (int(part) for part in name.split(","))
                return self.rgb(text, red, green, blue)
            except ValueError:
                return self.cyan(text)
        if name in ANSI_CODES:
            return self.style(name, text)
        return self.cyan(text)

    def red(self, text):
        """Return ``text`` styled red."""
        return self.style("red", text)

    def yellow(self, text):
        """Return ``text`` styled yellow."""
        return self.style("yellow", text)

    def green(self, text):
        """Return ``text`` styled green."""
        return self.style("green", text)

    def blue(self, text):
        """Return ``text`` styled blue."""
        return self.style("blue", text)

    def magenta(self, text):
        """Return ``text`` styled magenta."""
        return self.style("magenta", text)

    def dim(self, text):
        """Return ``text`` styled dim."""
        return self.style("dim", text)

    def bold(self, text):
        """Return ``text`` styled bold."""
        return self.style("bold", text)

    def italic(self, text):
        """Return ``text`` styled italic."""
        return self.style("italic", text)

    def cyan(self, text):
        """Return ``text`` styled cyan."""
        return self.style("cyan", text)

    def visible_len(self, text):
        """Return the printable width of ``text``, ignoring ANSI escape codes."""
        return len(_ANSI_RE.sub("", text))

    def pad(self, text, width, align="left"):
        """Justify ``text`` to ``width`` columns, measuring past any ANSI codes.

        Args:
            text: The (possibly already styled) text to pad.
            width: Target column width.
            align: ``"left"``, ``"right"``, or ``"center"``.

        Returns:
            ``text`` padded with spaces, or unchanged when already wide enough.
        """
        gap = width - self.visible_len(text)
        if gap <= 0:
            return text
        if align == "right":
            return " " * gap + text
        if align == "center":
            left = gap // 2
            return " " * left + text + " " * (gap - left)
        return text + " " * gap

    def width(self):
        """Return the terminal width in columns, falling back to 80."""
        return shutil.get_terminal_size((80, 24)).columns

    def print(self, text=""):
        """Write ``text`` followed by a newline to the output stream."""
        self.stream.write(text + "\n")

    def warn(self, text):
        """Write ``text`` followed by a newline to standard error."""
        sys.stderr.write(text + "\n")
