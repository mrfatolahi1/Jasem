"""jasem — a plain-text task manager and time tracker with pluggable AI parsing.

The package is organised in layers, each in its own sub-package:
:mod:`jasem.domain` holds the data models, :mod:`jasem.infrastructure` persists
them and talks to AI backends, :mod:`jasem.application` turns text into tasks
and runs the commands, :mod:`jasem.interface` drives and renders the CLI, and
:mod:`jasem.shared` holds primitives used across them.
"""

__version__ = "0.8.1"
