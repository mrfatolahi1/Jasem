"""Naming and locating the Markdown file behind each named task list.

The unnamed default list keeps the configured task file (``~/.jasem/tasks.md``);
every named list is a sibling file, ``tasks-<name>.md``. Deriving the path from
the configured file rather than a fixed directory keeps ``JASEM_FILE`` working.
"""

import glob
import os
import re

DEFAULT_NAME = "default"
"""Display name of the unnamed list; also accepted as a selector."""

DEFAULT_WORDS = {"", "-", DEFAULT_NAME}
"""Selector values that mean 'the unnamed default list'."""

_VALID = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
"""List names allowed on disk; anything else could escape the data directory."""


def normalize(name):
    """Return ``name`` as a canonical list name.

    A leading ``@`` is optional, case and surrounding space are ignored, and the
    words in :data:`DEFAULT_WORDS` select the unnamed list.

    Args:
        name: Raw selector text, e.g. ``"@Work"``.

    Returns:
        The lower-cased name, ``""`` for the default list, or ``None`` when the
        text is not a usable list name.
    """
    cleaned = (name or "").strip().lstrip("@").strip().lower()
    if cleaned in DEFAULT_WORDS:
        return ""
    return cleaned if _VALID.match(cleaned) else None


def path_for(task_file, name):
    """Return the file holding the list called ``name``.

    Args:
        task_file: The configured default task file.
        name: A normalized list name; ``""`` for the default list.

    Returns:
        ``task_file`` itself for the default list, otherwise its
        ``<stem>-<name>.md`` sibling.
    """
    if not name:
        return task_file
    stem, extension = os.path.splitext(task_file)
    return f"{stem}-{name}{extension or '.md'}"


def discover(task_file):
    """Return the names of the named lists that exist beside ``task_file``.

    The default list is never included — it is always available, whether or not
    its file has been written yet.

    Args:
        task_file: The configured default task file.

    Returns:
        Sorted list names, skipping files whose suffix is not a valid name.
    """
    stem, extension = os.path.splitext(task_file)
    prefix = f"{stem}-"
    names = set()
    for path in glob.glob(f"{prefix}*{extension or '.md'}"):
        candidate = normalize(path[len(prefix):-len(extension)] if extension else path[len(prefix):])
        if candidate:
            names.add(candidate)
    return sorted(names)


def label(name):
    """Return ``name`` as shown to the user, e.g. ``@work`` or ``default``."""
    return f"@{name}" if name else DEFAULT_NAME
