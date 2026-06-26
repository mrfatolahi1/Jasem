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


DESCRIPTION = "Handy plain-text task, time & expense tracker, with AI parsing"
REPO_URL = "https://github.com/mrfatolahi1/Jasem"
WIKI_URL = "https://github.com/mrfatolahi1/Jasem/wiki"


def render_logo(console):
    """Return the colored block wordmark, with a leading blank line."""
    lines = []
    for row, text in enumerate(LOGO_ROWS):
        painted = []
        for column, char in enumerate(text):
            if char == " ":
                painted.append(char)
            else:
                painted.append(console.rgb(char, *block_color(row, column)))
        lines.append("".join(painted))
    return "\n".join(["", *lines])


def render_version(console, version):
    """Return the ``jasem --version`` screen: logo, name + version, project link."""
    return "\n".join([
        render_logo(console),
        "",
        console.bold(f" Jasem {version}"),
        "",
        console.accent(f" {REPO_URL}"),
    ])


def render_welcome(console, version):
    """Return the no-args welcome screen: logo, what jasem is, and how to use it."""
    return "\n".join([
        render_logo(console),
        "",
        console.bold(f" Jasem {version}") + console.dim("  ·  " + DESCRIPTION),
        "",
        console.bold(" How to Use:"),
        "",
        console.green(" jasem --help"),
        console.accent(f" {WIKI_URL}"),
    ])
