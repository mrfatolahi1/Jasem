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
jasem todo            # open tasks, soonest deadline first
jasem track report    # time totals, by-tag & timeline
jasem acc report      # spending totals, by-tag & timeline
jasem                 # welcome screen
jasem --help          # full command reference
```

If no AI model is reachable, entries still save (dates parsed by regex).

## Commands

Three symmetric namespaces, same verbs in each — prefix every command with `jasem`:

| Action | `todo` — tasks | `track` — time | `acc` — spending |
|---|---|---|---|
| **Add** (natural language) | `todo "pay rent friday, finance"` | `track "1h30min review, work"` | `acc "50k lunch, food"` |
| **List** | `todo list [tag]` | `track list [period] [tag]` | `acc list [period] [tag]` |
| **Report** (totals · by-tag · timeline) | — | `track report [period] [tag]` | `acc report [period] [tag]` |
| **Filtered views** | `todo today · week · overdue · all` | — | — |
| **Search** | `todo find "rent"` | — | — |
| **Categories** | `todo tags` | `track tags` | `acc tags` |
| **Mark done** | `todo done <id>` | — | — |
| **Edit a field** | `todo set <id> deadline tomorrow` | `track set <id> time 2h` | `acc set <id> amount 60k` |
| **Remove** | `todo rm <id>` | `track rm <id>` | `acc rm <id>` |

`period` = `today` · `week` · `month` · `all`. Lists and reports render as aligned tables with bar charts and sparklines.

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

## Persian (Jalali) calendar

Set `JASEM_JALALI=true` to read and show every date in the Persian (Jalali/Shamsi) calendar:

```sh
export JASEM_JALALI=true
jasem todo "pay rent 1405-04-10, finance"   # type dates in Jalali
jasem todo list                              # dates shown in Jalali
```

Dates you **type** and dates jasem **shows** are Jalali, but files on disk stay Gregorian ISO (`YYYY-MM-DD`) — so the same data works with or without the flag. Relative phrases (`tomorrow`, `next friday`, `in 3 days`) work in both modes. Leave it unset (or `false`) for the default Gregorian calendar.

## Config

- **Storage** — `~/.jasem/*.md`; grep, edit, sync, or version-control it freely.
- **Color** — `JASEM_ACCENT` recolors the accent; `NO_COLOR` forces plain text.

Run `jasem --help` for every command, option, and environment variable.

## A note on AI

**I used AI to create some parts of Jasem, but I carefully reviewed all the code written by AI rather than blindly copy-pasting.**

## License

MIT — see [LICENSE](LICENSE).
