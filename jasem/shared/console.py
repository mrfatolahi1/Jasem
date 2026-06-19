"""Terminal output styling.

:class:`Console` applies ANSI color codes only when standard output is an
interactive terminal, so redirected or piped output stays plain text.
"""

import sys

ANSI_CODES = {
    "red": "31",
    "yellow": "33",
    "green": "32",
    "dim": "2",
    "bold": "1",
    "cyan": "36",
}


class Console:
    """Writes styled text to an output stream, coloring only a real terminal."""

    def __init__(self, stream=None):
        """Bind the console to a stream and detect terminal support.

        Args:
            stream: Output stream. Defaults to ``sys.stdout``.
        """
        self.stream = stream if stream is not None else sys.stdout
        self.color = bool(getattr(self.stream, "isatty", lambda: False)())

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

    def red(self, text):
        """Return ``text`` styled red."""
        return self.style("red", text)

    def yellow(self, text):
        """Return ``text`` styled yellow."""
        return self.style("yellow", text)

    def green(self, text):
        """Return ``text`` styled green."""
        return self.style("green", text)

    def dim(self, text):
        """Return ``text`` styled dim."""
        return self.style("dim", text)

    def bold(self, text):
        """Return ``text`` styled bold."""
        return self.style("bold", text)

    def cyan(self, text):
        """Return ``text`` styled cyan."""
        return self.style("cyan", text)

    def print(self, text=""):
        """Write ``text`` followed by a newline to the output stream."""
        self.stream.write(text + "\n")

    def warn(self, text):
        """Write ``text`` followed by a newline to standard error."""
        sys.stderr.write(text + "\n")
