![jasem](docs/logo.svg)

# jasem

A plain-text **task manager**, **time tracker**, and **spending log** for your terminal — natural-language input, pluggable AI parsing, zero dependencies. Your data stays in human-readable Markdown under `~/.jasem/`.

📖 **[Full guide & command reference → the wiki](https://github.com/mrfatolahi1/Jasem/wiki)**

## Install

Needs Python 3.8+.

```sh
pipx install jasem   # or: pip install jasem
```

## Quick start

```sh
# Capture — write naturally; jasem reads the deadline, amount & tags for you
jasem todo  "pay rent next friday, high priority, finance"
jasem track "1h30min code review, work"
jasem acc   "50k lunch with the team, food"

# Review
jasem todo          # open tasks, soonest deadline first
jasem               # welcome screen
jasem --help        # full command reference
```

If no AI model is reachable, entries still save (dates parsed by regex).

## Commands

Three symmetric namespaces, each sharing the same verbs — a quoted `"<text>"` adds; then `list`, `tags`, `rm`, `set`:

| Namespace | Tracks | Example |
|---|---|---|
| `todo` | tasks | `jasem todo "submit report by friday, work"` |
| `track` | time | `jasem track "1h30min debugging, work"` |
| `acc` | spending | `jasem acc "50k lunch, food"` |

Views & reports — `list` · `today` · `week` · `overdue` · `find` · `report` `[period] [tag]` — render as aligned tables with bar charts and sparklines.

## AI backend

Parsing is the only step that uses a model. Default is local **[Ollama](https://ollama.com)** (free, private, offline).

```sh
# Local (default)
ollama serve && ollama pull qwen2.5:3b

# OpenAI-compatible (OpenAI, Groq, OpenRouter, LM Studio, …)
export JASEM_PROVIDER=openai JASEM_API_KEY=sk-...
export JASEM_OPENAI_API_BASE=https://openrouter.ai/api/v1   # for non-OpenAI hosts

# Anthropic (Claude)
export JASEM_PROVIDER=anthropic JASEM_API_KEY=sk-ant-...
```

## Config

- **Storage** — `~/.jasem/*.md`; grep, edit, sync, or version-control it freely.
- **Calendar** — `JASEM_JALALI=true` shows & reads dates in the Persian (Jalali) calendar; files on disk stay Gregorian ISO.
- **Color** — `JASEM_ACCENT` recolors the accent; `NO_COLOR` forces plain text.

Run `jasem --help` for every command, option, and environment variable.

## License

MIT — see [LICENSE](LICENSE).
