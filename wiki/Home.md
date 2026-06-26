# jasem

A plain-text **task manager**, **time tracker**, and **spending log** for your
terminal, with pluggable AI parsing. Zero dependencies, your data in
human-readable Markdown, fully offline by default.

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

You write in plain language; jasem extracts the deadline, priority, and tags for
you. Everything is stored as Markdown in `~/.jasem/` — grep it, edit it,
version-control it, sync it however you like.

## The idea in one minute

Everything is organised into **three symmetric namespaces** that share the same
verbs:

| Namespace | What it tracks | Add example |
|-----------|----------------|-------------|
| **`todo`** | tasks / to-dos | `jasem todo "submit report by friday, work"` |
| **`track`** | time spent | `jasem track "1h30min code review, work"` |
| **`acc`** | money spent | `jasem acc "50k lunch with the team, food"` |

Each namespace understands the same verbs: a quoted **`"<text>"`** adds an entry,
then **`list`**, **`tags`**, **`rm`**, and **`set`** view and manage what you
already have (plus `report` for `track`/`acc`, and task-specific views for
`todo`). Run **`jasem`** alone for a one-screen [[Dashboard]].

## Start here

* **[[Installation]]** — install with pipx or pip (Python 3.8+)
* **[[Quick Start]]** — the core loop in five minutes

## Using jasem

* **[[Tasks]]** — `jasem todo`: add, view, search, complete, edit
* **[[Time Tracking]]** — `jasem track`: log time, list, report
* **[[Spending]]** — `jasem acc`: record spending, list, report
* **[[Dashboard]]** — the no-arguments home screen
* **[[Natural Language Input]]** — how dates, durations, and amounts are parsed

## Configuration & internals

* **[[AI Backends]]** — Ollama (default), OpenAI-compatible, or Anthropic
* **[[Configuration]]** — every environment variable and file location
* **[[Jalali Calendar]]** — working in the Persian (Shamsi) calendar
* **[[Data Files]]** — the on-disk Markdown format and hand-editing

## Reference

* **[[Command Reference]]** — a one-page cheat-sheet of every command
* **[[FAQ]]** — troubleshooting and common questions

---

jasem is MIT-licensed. Source: <https://github.com/mrfatolahi1/jasem>
