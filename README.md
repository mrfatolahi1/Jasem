# jasem

A plain-text **task manager** and **time tracker** for your terminal.

You write tasks in natural language; an AI backend extracts the structure
(title, deadline, priority, tags) and plain Python turns the deadline phrase
into a real date. Everything is stored in a human-readable Markdown table, so
you can read, grep, edit, sync, or version-control it however you like.

- **Zero dependencies.** A single Python file using only the standard library.
- **Local by default.** Works fully offline with [Ollama](https://ollama.com).
- **Bring your own AI.** Point it at any OpenAI-compatible API or at Anthropic
  with two environment variables — no code changes.
- **Degrades gracefully.** If no model is reachable, your task is still saved
  (dates are parsed with regex; you just don't get auto title/priority/tags).

```text
$ jasem "pay rent next friday, high priority, finance"
✓ added #1: pay rent
  priority=high  deadline=2026-06-19  tags=finance

$ jasem today
Due today
  ☐   2  [medium]  2026-06-15 (today)  call dentist  #health

$ jasem track "1h 30min, code review, work"
✓ tracked 1h 30min · code review · today · #work
```

## Install

jasem needs **Python 3.8+** and nothing else.

### With pipx (recommended)

```sh
pipx install .
# or straight from a checkout / git URL once you publish it:
# pipx install git+https://github.com/your-username/jasem
```

### With pip

```sh
pip install .
```

Both install a `jasem` command on your `PATH`.

### No install at all

It's one file — copy it and run it:

```sh
cp jasem.py ~/.local/bin/jasem && chmod +x ~/.local/bin/jasem
```

## Choosing an AI backend

Natural-language parsing is the only step that uses a model. Pick a backend
with `JASEM_PROVIDER`; the rest is config via environment variables.

### Ollama (default — local, free, private)

```sh
ollama serve
ollama pull qwen2.5:3b        # or any model you like
jasem "submit report by friday, work"
```

No keys, nothing leaves your machine. Override the model with
`JASEM_MODEL=qwen2.5:7b` and the host with `OLLAMA_HOST`.

### Any OpenAI-compatible API (OpenAI, Groq, OpenRouter, Together, LM Studio, vLLM, …)

```sh
export JASEM_PROVIDER=openai
export JASEM_API_KEY=sk-...
export JASEM_MODEL=gpt-4o-mini          # default for this provider
# For a non-OpenAI host, also set the base URL:
export JASEM_API_BASE=https://api.groq.com/openai/v1
```

### Anthropic (Claude)

```sh
export JASEM_PROVIDER=anthropic
export JASEM_API_KEY=sk-ant-...
export JASEM_MODEL=claude-opus-4-8       # default; e.g. claude-haiku-4-5 for cheaper/faster
```

Put whichever block you use in your shell profile (`~/.zshrc`, `~/.bashrc`) so
it's set for every session.

## Commands

```text
ADD
  jasem "pay rent next friday, high priority, finance"
  jasem add "..."            force-add even if the text starts with a command word

VIEW                          (append a category to filter, e.g. jasem list work)
  jasem list  (ls)           open tasks, soonest deadline first
  jasem today                due today
  jasem week                 due within the next 7 days
  jasem overdue              past deadline, not done
  jasem all                  everything, including completed
  jasem tags                 list categories in use, with counts

UPDATE
  jasem done <id>...         mark task(s) complete
  jasem rm <id>...           delete task(s)
  jasem set <id> priority    high | medium | low
  jasem set <id> deadline    next friday | in 3 days | 2026-07-01 | none
  jasem set <id> category    work finance      (space/comma-separated; "none" clears)

TIME TRACKING                 format: "<time>, <work>[, <date>][, <tag>]"
  jasem track "2h, coding"
  jasem track "30 min, coding, yesterday, work"
  jasem track                today's entries, with a daily total
  jasem track week           last 7 days, grouped by day
  jasem track all [tag]      everything; optional tag filter

jasem help                    full, colorized help
```

Run `jasem help` for the complete reference.

## Configuration

| Env var            | Default                         | Purpose                                              |
|--------------------|---------------------------------|------------------------------------------------------|
| `JASEM_PROVIDER`   | `ollama`                        | `ollama` \| `openai` \| `anthropic`                  |
| `JASEM_MODEL`      | per provider                    | Model id                                             |
| `JASEM_API_KEY`    | —                               | Key for openai/anthropic (also reads `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`) |
| `JASEM_API_BASE`   | provider default                | Base URL for any OpenAI-compatible / custom endpoint |
| `OLLAMA_HOST`      | `http://localhost:11434`        | Ollama daemon address                                |
| `JASEM_DIR`        | `~/.jasem`                      | Where data is stored                                 |
| `JASEM_FILE`       | `$JASEM_DIR/tasks.md`           | Tasks file                                           |
| `JASEM_TRACK_FILE` | `$JASEM_DIR/timelog.md`         | Time-log file                                        |

## How storage works

`tasks.md` and `timelog.md` are ordinary Markdown tables. You can hand-edit
rows, keep them in a synced folder, or commit them to a private repo — just
keep the column order intact. jasem reads and rewrites the whole file on each
write, preserving your edits.

## Writing good tasks

Clearer cues parse better:

- **deadline:** `tomorrow`, `next friday`, `in 3 days`, `june 20`, `2026-07-01` (avoid `asap`/`soon`)
- **priority:** say `high` or `low` (default `medium`; avoid `urgent`/`important`)
- **category:** name it plainly — `work`, `finance`, `university`
- **pattern:** `"<what> by <when>, <priority>, <category>"`

## License

MIT — see [LICENSE](LICENSE).
