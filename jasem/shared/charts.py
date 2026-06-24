"""Drawing of horizontal bar charts from Unicode block glyphs.

Keeps reporting free of any charting dependency: a bar is just a run of full
blocks plus, for the leftover fraction, one of the eighth-width partial blocks.
"""

BAR_WIDTH = 24
"""Default width, in characters, of a full-length bar."""

_EIGHTHS = " ▏▎▍▌▋▊▉█"
"""Block glyphs from empty (index 0) to a full cell (index 8), by eighths."""


def bar(value, max_value, width=BAR_WIDTH):
    """Return a horizontal bar whose length is ``value`` relative to ``max_value``.

    The bar is rendered with full blocks (``█``) and a single trailing partial
    block for sub-character precision, so small differences stay visible.

    Args:
        value: The magnitude to draw.
        max_value: The magnitude that fills the whole ``width``.
        width: Length, in characters, of a full bar.

    Returns:
        The bar string, or ``""`` when there is nothing to draw.
    """
    if max_value <= 0 or value <= 0:
        return ""
    eighths = int(round(value / max_value * width * 8))
    eighths = min(eighths, width * 8)
    full, remainder = divmod(eighths, 8)
    return "█" * full + (_EIGHTHS[remainder] if remainder else "")
