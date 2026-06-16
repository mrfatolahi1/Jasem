"""Command-line entry point and argument routing."""

import sys

from .app import App
from .config import Config
from .console import Console


def main(argv=None):
    """Run the jasem command-line interface.

    Args:
        argv: Argument list excluding the program name. Defaults to
            ``sys.argv[1:]`` so this works directly as a console-script entry
            point.
    """
    arguments = list(sys.argv[1:] if argv is None else argv)
    App(Config(), Console()).run(arguments)
