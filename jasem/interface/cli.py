"""Command-line entry point and argument routing."""

import sys

from ..application.app import App
from ..shared.config import Config
from ..shared.console import Console


def main(argv=None):
    """Run the jasem command-line interface.

    Args:
        argv: Argument list excluding the program name. Defaults to
            ``sys.argv[1:]`` so this works directly as a console-script entry
            point.
    """
    arguments = list(sys.argv[1:] if argv is None else argv)
    App(Config(), Console()).run(arguments)
