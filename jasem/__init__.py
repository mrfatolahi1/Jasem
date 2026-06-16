"""jasem — a plain-text task manager and time tracker with pluggable AI parsing.

The package is organised in layers: :mod:`jasem.domain` holds the data models,
:mod:`jasem.storage` persists them as Markdown tables, :mod:`jasem.providers`
talks to AI backends, :mod:`jasem.parsing` turns text into task fields, and
:mod:`jasem.app` / :mod:`jasem.cli` form the command-line interface.
"""

__version__ = "0.3.0"
