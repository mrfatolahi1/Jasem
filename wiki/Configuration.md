# Configuration

jasem has **no config file** — everything is controlled by environment variables,
read once at startup. Set them in your shell profile (`~/.zshrc`, `~/.bashrc`,
…). To confirm what jasem actually resolved, run `jasem help`; it prints the
active provider, model, and file paths at the bottom.

## Files & directories

| Variable | Default | Controls |
|----------|---------|----------|
| `JASEM_DIR` | `~/.jasem` | the data directory |
| `JASEM_FILE` | `<JASEM_DIR>/tasks.md` | the tasks file (default list) |
| `JASEM_LIST` | — | the task list used when no `@name` is given |
| `JASEM_TRACK_FILE` | `<JASEM_DIR>/timelog.md` | the time-log file |
| `JASEM_SPEND_FILE` | `<JASEM_DIR>/spending.md` | the spending file |

`~` is expanded in all of these. Point them at a synced folder (Dropbox, a git
repo, etc.) to back up or share your data — see [[Data Files]].

```sh
export JASEM_DIR=~/Dropbox/jasem            # move everything at once
export JASEM_FILE=~/work/tasks.md           # or relocate one file
export JASEM_LIST=work                      # default to the "work" list
```

Named lists are stored beside `JASEM_FILE` as `tasks-<name>.md`, so relocating
the tasks file moves every list with it. See [[Tasks]] for the `@<list>`
selector.

## AI provider

| Variable | Default | Controls |
|----------|---------|----------|
| `JASEM_PROVIDER` | `ollama` | `ollama` · `openai` · `anthropic` |
| `JASEM_MODEL` | per-provider* | the model id |
| `JASEM_API_KEY` | — | API key for `openai`/`anthropic` |
| `JASEM_OPENAI_API_BASE` | — | base URL for OpenAI-compatible hosts |
| `JASEM_API_BASE` | — | generic base-URL fallback |
| `OLLAMA_HOST` | `http://localhost:11434` | the Ollama server |

\* Default model: `qwen2.5:3b` (ollama), `gpt-4o-mini` (openai),
`claude-opus-4-8` (anthropic).

**Also recognised (fallbacks):** the API key falls back to `OPENAI_API_KEY` then
`ANTHROPIC_API_KEY`; the OpenAI base URL falls back through
`JASEM_OPENAI_BASE_URL` → `OPENAI_BASE_URL` → `JASEM_API_BASE`. Full details and
examples are on the [[AI Backends]] page.

## Calendar

| Variable | Default | Controls |
|----------|---------|----------|
| `JASEM_JALALI` | unset (Gregorian) | set to `1`/`true`/`yes`/`on` for the Persian (Jalali) calendar |

Data on disk always stays Gregorian ISO, so the same files work with the flag on
or off. See [[Jalali Calendar]].

## Colour & appearance

| Variable | Default | Controls |
|----------|---------|----------|
| `JASEM_ACCENT` | `cyan` | accent colour — a name (`green`, `magenta`, …) or `r,g,b` |
| `NO_COLOR` | unset | set (to anything) to force plain, uncoloured output |
| `FORCE_COLOR` | unset | set to force colour even when output isn't a terminal |

Colour is on automatically when writing to a terminal. `NO_COLOR` wins when you
want clean text for piping or logging; `FORCE_COLOR` is handy when piping into a
pager that interprets colour.

```sh
export JASEM_ACCENT=magenta
export JASEM_ACCENT=255,128,0     # an orange accent via RGB
```

## A sample profile block

```sh
# ~/.zshrc — jasem
export JASEM_DIR=~/Dropbox/jasem
export JASEM_PROVIDER=ollama
export JASEM_MODEL=qwen2.5:3b
export JASEM_ACCENT=cyan
# export JASEM_JALALI=true        # uncomment for the Persian calendar
```

## Full variable list

`JASEM_DIR` · `JASEM_FILE` · `JASEM_TRACK_FILE` · `JASEM_SPEND_FILE` ·
`JASEM_PROVIDER` · `JASEM_MODEL` · `JASEM_API_KEY` · `JASEM_OPENAI_API_BASE` ·
`JASEM_API_BASE` · `OLLAMA_HOST` · `JASEM_JALALI` · `JASEM_ACCENT` — plus the
standard `NO_COLOR` / `FORCE_COLOR`, and the fallbacks `OPENAI_API_KEY`,
`ANTHROPIC_API_KEY`, `JASEM_OPENAI_BASE_URL`, `OPENAI_BASE_URL`.

## See also

* [[AI Backends]] · [[Jalali Calendar]] · [[Data Files]]
