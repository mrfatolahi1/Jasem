"""A tiny, dependency-free layout toolkit for the terminal.

Two primitives compose every list, report, and dashboard view:

* :func:`rule` — a light horizontal divider carrying an optional left title and
  right-aligned summary, the frame around each section.
* :class:`Table` — width-aware aligned columns that truncate gracefully when the
  terminal is narrow, with per-cell styling.

All width maths go through :class:`~jasem.shared.console.Console`'s
``visible_len``/``pad``/``width`` helpers so styled (ANSI-wrapped) cells stay
aligned. Nothing here imports anything outside the standard library.
"""

MAX_WIDTH = 84
"""Widest a rule or table is allowed to grow, so output stays readable."""

INDENT = " "
"""Left margin shared by rules and table rows."""


def rule(console, title="", summary="", width=None):
    """Return a horizontal rule, optionally titled on the left and summarised right.

    Args:
        console: Console used for styling and width detection.
        title: Bold accent text shown at the start of the rule.
        summary: Dim text shown flush against the right end.
        width: Total width; defaults to the terminal width, capped at
            :data:`MAX_WIDTH`.

    Returns:
        The composed rule as a single string.
    """
    total = width or min(console.width(), MAX_WIDTH)
    left = INDENT
    if title:
        left += console.bold(console.accent(title)) + " "
    right = ""
    if summary:
        right = " " + console.dim(summary) + " "
    fill = total - console.visible_len(left) - console.visible_len(right)
    return left + console.dim("─" * max(2, fill)) + right


def truncate(text, width):
    """Return ``text`` shortened to ``width`` columns with a trailing ``…``."""
    if width <= 0:
        return ""
    if len(text) <= width:
        return text
    if width == 1:
        return "…"
    return text[: width - 1] + "…"


class Column:
    """One column's alignment, styling, and sizing rules for a :class:`Table`."""

    def __init__(self, align="left", style=None, flex=False, min_width=1, max_width=None):
        """Configure the column.

        Args:
            align: ``"left"``, ``"right"``, or ``"center"``.
            style: Callable applied to each padded cell (e.g. ``console.dim``),
                used when a cell does not carry its own style.
            flex: Whether this column yields width first when the row is too wide.
            min_width: Smallest width this column may shrink to.
            max_width: Largest natural width before cells are truncated.
        """
        self.align = align
        self.style = style
        self.flex = flex
        self.min_width = min_width
        self.max_width = max_width


class Table:
    """Renders rows of cells as aligned, width-aware columns (no borders)."""

    def __init__(self, console, columns, gap=2, indent=INDENT):
        """Bind the table to a console and its column definitions.

        Args:
            console: The output :class:`~jasem.shared.console.Console`.
            columns: A list of :class:`Column` definitions, one per cell.
            gap: Spaces between adjacent columns.
            indent: Left margin string for every row.
        """
        self.console = console
        self.columns = columns
        self.gap = gap
        self.indent = indent

    def render(self, rows):
        """Return the rendered rows as a list of strings.

        Each row is a list of cells. A cell is either a plain string (styled with
        its column's default style) or a ``(text, style)`` pair whose ``style``
        callable — or ``None`` for no styling — overrides the column default.

        Long cells in flexible columns are truncated with ``…`` so rows fit the
        terminal width.
        """
        console = self.console
        normalized = [[self._normalize(cell, column)
                       for cell, column in zip(row, self.columns)] for row in rows]
        widths = self._column_widths(normalized)
        lines = []
        for row in normalized:
            cells = []
            last = len(row) - 1
            for index, (text, style) in enumerate(row):
                column = self.columns[index]
                shown = truncate(text, widths[index])
                ragged = index == last and column.align == "left"
                padded = shown if ragged else console.pad(shown, widths[index], column.align)
                cells.append(style(padded) if style else padded)
            line = self.indent + (" " * self.gap).join(cells)
            lines.append(line.rstrip())
        return lines

    def _normalize(self, cell, column):
        """Return ``cell`` as a ``(plain_text, style)`` pair."""
        if isinstance(cell, tuple):
            text, style = cell
            return str(text), style
        return str(cell), column.style

    def _column_widths(self, rows):
        """Return the final width of each column after fitting to the terminal."""
        count = len(self.columns)
        widths = [0] * count
        for row in rows:
            for index, (text, _) in enumerate(row):
                widths[index] = max(widths[index], len(text))
        for index, column in enumerate(self.columns):
            if column.max_width is not None:
                widths[index] = min(widths[index], column.max_width)
        available = min(self.console.width(), MAX_WIDTH) - len(self.indent)
        available -= self.gap * (count - 1)
        self._shrink_to_fit(widths, available)
        return widths

    def _shrink_to_fit(self, widths, available):
        """Trim flexible columns in place until ``widths`` fit ``available``."""
        flexible = [index for index, column in enumerate(self.columns) if column.flex]
        if not flexible:
            flexible = [max(range(len(widths)), key=lambda index: widths[index])]
        while sum(widths) > available:
            widest = max(flexible, key=lambda index: widths[index])
            if widths[widest] <= self.columns[widest].min_width:
                break
            widths[widest] -= 1
