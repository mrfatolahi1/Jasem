"""The colorful ASCII wordmark shown by ``jasem --version``.

The logo is a fixed block-character wordmark. Each block is painted from a small
cool-toned palette, indexed so neighbouring blocks never share a color. Coloring
goes through :meth:`Console.rgb`, which returns each character unchanged when
color is disabled, so the same code path prints plain art when output is piped or
``NO_COLOR`` is set.
"""

LOGO_ROWS = (
    " ▀▀█ █▀█ █▀▀ █▀▀ █▀█▀█",
    " ▄ █ █▀█ ▀▀█ █▀▀ █ ▀ █",
    " ▀▀▀ ▀ ▀ ▀▀▀ ▀▀▀ ▀   ▀",
)
"""The wordmark, one string per row; spaces are gaps, blocks are letters."""

PALETTE = (
    (216, 166, 87),   # gold
    (224, 123, 57),   # orange
    (196, 78, 59),    # brick red
    (138, 75, 107),   # plum
    (90, 109, 168),   # slate blue
)
"""Atari-style warm-retro colors cycled across the blocks (no gradient)."""


def block_color(row, column):
    """Return the palette color for the block at ``row``/``column``.

    Indexing by ``row + column`` shifts the color by one for every horizontal or
    vertical step, so no two edge-adjacent blocks share a color.
    """
    return PALETTE[(row + column) % len(PALETTE)]


def render_logo(console, version):
    """Return the colored wordmark plus a version line as one printable string.

    Args:
        console: Console used to color the characters.
        version: The version string shown under the logo.

    Returns:
        The logo, a blank line, and a dim ``jasem <version>`` footer.
    """
    lines = []
    for row, text in enumerate(LOGO_ROWS):
        painted = []
        for column, char in enumerate(text):
            if char == " ":
                painted.append(char)
            else:
                painted.append(console.rgb(char, *block_color(row, column)))
        lines.append("".join(painted))
    return "\n".join(["", *lines, "", console.dim(f" jasem {version}")])
