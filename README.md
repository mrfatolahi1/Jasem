<p align="center">
  <img src="docs/logo.svg" alt="jasem" width="420">
</p>

# jasem

A plain-text **task manager**, **time tracker**, and **spending log** for your
terminal, with pluggable AI parsing. One file, zero dependencies, your data in
human-readable Markdown.

## Install & run

Needs **Python 3.8+**.

```sh
pipx install jasem      # recommended — isolated, puts `jasem` on your PATH
# or
pip install jasem
```

Then write a task in plain language and see what's due:

```text
$ jasem todo "pay rent next friday, high priority, finance"
✓ added #1: pay rent
  priority=high  deadline=2026-06-19  tags=finance

$ jasem todo
 Open tasks ──────────────────────────────────────────────
 ●  1  ⚑ high  in 4d  pay rent      #finance  today
 ●  2    med   today  call dentist  #health   2d
 ──────────────────────────── 2 open  ·  1 due today
```

That's the whole loop: write naturally, jasem extracts the deadline, priority,
and tags for you. Deadlines show as relative time (`in 4d`, `today`, `overdue`)
and the last column is each task's age.

Run **`jasem`** with no arguments for a one-screen **dashboard** — what needs
attention today, plus the time you've tracked and spent — drawn straight from
your logs, fully offline.

Everything is organized into three symmetric namespaces — **`todo`** (tasks),
**`track`** (time), and **`acc`** (spending) — and each shares the same verbs:
a quoted `"<text>"` adds, then `list`, `tags`, `rm`, and `set`. Lists and
reports render as aligned, width-aware tables with bar charts and sparklines;
set `JASEM_ACCENT` to recolor the accent, or `NO_COLOR` for plain text.

## Features

- **Natural-language tasks** — `jasem todo "submit report by friday, work"`
  becomes a title, deadline, priority, and tags.
- **Views, search & edits** — `jasem todo list`, `today`, `week`, `overdue`,
  `tags`, `find rent`, `done 3`, `set 3 deadline tomorrow`, `rm 3`.
- **Time tracking** — `jasem track "1h 30min, code review, work"`, then
  `jasem track list` to see entries and `jasem track report week` for per-day
  totals; fix or drop an entry with `jasem track set 3 time 2h` and
  `jasem track rm 3`.
- **Spending log** — `jasem acc "50k lunch with the team, food"` records the
  amount, date, and category; review with `jasem acc list` and
  `jasem acc report month`; edit or drop with `jasem acc set 3 amount 60k` and
  `jasem acc rm 3`.
- **Plain-text storage** — everything lives in `~/.jasem/*.md`; read, grep,
  edit, sync, or version-control it however you like.
- **Pluggable AI, local by default** — runs fully offline with
  [Ollama](https://ollama.com), or point it at any OpenAI-compatible API or
  Anthropic. If no model is reachable, tasks still save (dates parsed by regex).

## Choosing an AI backend

Parsing is the only step that uses a model — pick one with environment variables:

```sh
# Local, free, private (default) — just have Ollama running
ollama serve && ollama pull qwen2.5:3b

# Any OpenAI-compatible API (OpenAI, Groq, OpenRouter, LM Studio, …)
export JASEM_PROVIDER=openai JASEM_API_KEY=sk-...
export JASEM_OPENAI_API_BASE=https://openrouter.ai/api/v1  # or OPENAI_BASE_URL

# Anthropic (Claude)
export JASEM_PROVIDER=anthropic JASEM_API_KEY=sk-ant-...
```

## Persian (Jalali) calendar

Set `JASEM_JALALI=true` to work in the Persian (Jalali/Shamsi) calendar:

```sh
export JASEM_JALALI=true
jasem todo "pay rent 1405-04-10, finance"   # type deadlines in Jalali
jasem todo list                              # dates are shown in Jalali
```

Every date jasem **shows** is Jalali and every explicit date you **type** is read
as Jalali — but your data on disk stays Gregorian ISO (`YYYY-MM-DD`), so the same
files work with or without the flag. Relative phrases (`tomorrow`, `next friday`,
`in 3 days`) work in both modes. Leave the variable unset (or `false`) for the
default Gregorian calendar.

## More

Run **`jasem help`** for the full command reference, every option, and all
configuration variables, or **`jasem version`** to check what you have installed.

## License

MIT — see [LICENSE](LICENSE).
