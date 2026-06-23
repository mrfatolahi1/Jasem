# jasem

A plain-text **task manager** and **time tracker** for your terminal, with
pluggable AI parsing. One file, zero dependencies, your data in human-readable
Markdown.

## Install & run

Needs **Python 3.8+**.

```sh
pipx install jasem      # recommended — isolated, puts `jasem` on your PATH
# or
pip install jasem
```

Then write a task in plain language and see what's due:

```text
$ jasem "pay rent next friday, high priority, finance"
✓ added #1: pay rent
  priority=high  deadline=2026-06-19  tags=finance

$ jasem today
Due today
  ☐   2  [medium]  2026-06-15 (today)  call dentist  #health
```

That's the whole loop: write naturally, jasem extracts the deadline, priority,
and tags for you.

## Features

- **Natural-language tasks** — `jasem "submit report by friday, work"` becomes
  a title, deadline, priority, and tags.
- **Views & edits** — `jasem list`, `today`, `week`, `overdue`,
  `done 3`, `set 3 deadline tomorrow`, `rm 3`.
- **Time tracking** — `jasem track "1h 30min, code review, work"`, then
  `jasem track week` for per-day totals; fix or drop an entry with
  `jasem track set 3 time 2h` and `jasem track rm 3`.
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

## More

Run **`jasem help`** for the full command reference, every option, and all
configuration variables.

## License

MIT — see [LICENSE](LICENSE).
