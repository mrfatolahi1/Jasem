# Installation

jasem needs **Python 3.8 or newer** and has **no third-party dependencies**.

## Recommended: pipx

[pipx](https://pipx.pypa.io) installs jasem into its own isolated environment and
puts the `jasem` command on your `PATH` — the cleanest option for a CLI tool.

```sh
pipx install jasem
```

If you don't have pipx yet:

```sh
python3 -m pip install --user pipx
python3 -m pipx ensurepath      # then open a new shell
```

## Alternative: pip

```sh
pip install jasem
```

Use a virtual environment if you don't want to install into your system Python:

```sh
python3 -m venv ~/.venvs/jasem
~/.venvs/jasem/bin/pip install jasem
~/.venvs/jasem/bin/jasem version
```

## Verify the install

```sh
jasem version        # e.g. "jasem 1.0.0"   (also: jasem --version, jasem -v)
jasem help           # the full built-in command reference
jasem                # the dashboard (empty until you add something)
```

## First run

The first time you add something, jasem creates the data directory and files for
you — no setup, no config file:

```sh
jasem todo "try jasem out today"
```

This writes to `~/.jasem/` (`tasks.md`, `timelog.md`, `spending.md`). See
[[Data Files]] for the format and [[Configuration]] to move the directory
elsewhere.

## Optional: set up AI parsing

Out of the box, jasem expects a local [Ollama](https://ollama.com) model for the
best natural-language parsing — but **it works without one too**: if no model is
reachable, entries are still saved (dates parsed by a built-in regex). To get the
full experience either run Ollama locally or point jasem at a hosted API; see
**[[AI Backends]]**.

```sh
# Local, free, private (the default backend)
ollama serve
ollama pull qwen2.5:3b
```

## Upgrading

```sh
pipx upgrade jasem      # if installed with pipx
pip install -U jasem    # if installed with pip
```

Your data in `~/.jasem/` is never touched by an upgrade.

## Uninstalling

```sh
pipx uninstall jasem    # or: pip uninstall jasem
```

Your Markdown data files remain in `~/.jasem/`; delete that directory yourself if
you also want to remove your data.
