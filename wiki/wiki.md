# jasem — User Manual

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

---

## Contents

1. [Installation](#installation)
2. [Quick start](#quick-start)
3. [Core concepts](#core-concepts)
4. [Tasks](#tasks)
5. [Time tracking](#time-tracking)
6. [Spending](#spending)
7. [The dashboard](#the-dashboard)
8. [Natural language input](#natural-language-input)
9. [AI backends](#ai-backends)
10. [Configuration](#configuration)
11. [Persian (Jalali) calendar](#persian-jalali-calendar)
12. [Data files and storage](#data-files-and-storage)
13. [Command reference](#command-reference)
14. [FAQ and troubleshooting](#faq-and-troubleshooting)
15. [License](#license)

---

## Installation

jasem needs **Python 3.8 or newer** and has **no third-party dependencies**.

**Recommended — [pipx](https://pipx.pypa.io)** (isolated environment, puts `jasem`
on your `PATH`):

```sh
pipx install jasem
```

If you don't have pipx yet:

```sh
python3 -m pip install --user pipx
python3 -m pipx ensurepath      # then open a new shell
```

**Alternative — pip:**

```sh
pip install jasem
```

**Verify:**

```sh
jasem version        # e.g. "jasem 1.0.1"   (also: jasem --version, jasem -v)
jasem help           # the full built-in command reference
jasem                # the dashboard (empty until you add something)
```

The first time you add something, jasem creates `~/.jasem/` and its files for you
— no setup, no config file.

**Upgrade / uninstall:**

```sh
pipx upgrade jasem      # or: pip install -U jasem
pipx uninstall jasem    # or: pip uninstall jasem
```

Your data in `~/.jasem/` is never touched by an upgrade or uninstall.

**Optional — AI parsing.** Out of the box jasem expects a local
[Ollama](https://ollama.com) model for the best natural-language parsing, but it
works without one too: if no model is reachable, entries are still saved (dates
parsed by a built-in regex). For the full experience, run Ollama locally or point
jasem at a hosted API — see [AI backends](#ai-backends).

```sh
ollama serve
ollama pull qwen2.5:3b
```

---

## Quick start

**1. Add a task in plain language.** jasem pulls out the title, deadline,
priority, and tags:

```text
$ jasem todo "pay rent next friday, high priority, finance"
✓ added #1: pay rent
  priority=high  deadline=2026-06-19  tags=finance
```

> **Tip:** Quote the whole description. It keeps shell characters like `&`, `!`,
> `*`, `(`, `)` literal and keeps multi-word text together.

**2. See what's open.** A bare `jasem todo` lists open tasks, soonest deadline
first:

```text
$ jasem todo
 Open tasks ──────────────────────────────────────────────
 ●  1  ⚑ high  in 4d  pay rent      #finance  today
 ●  2    med   today  call dentist  #health   2d
 ──────────────────────────── 2 open  ·  1 due today
```

**3. Track some time:**

```text
$ jasem track "1h30min code review, work"
✓ tracked #1 1h 30min · code review · today · #work
```

**4. Log spending:**

```text
$ jasem acc "50k lunch with the team, food"
✓ recorded #1 50,000 · lunch with the team · today · #food
```

**5. Get the big picture** — run `jasem` with no arguments for a one-screen
[dashboard](#the-dashboard).

**6. Fix things by id** (the id is shown when you add and in every list):

```sh
jasem todo done 1                       # mark task #1 complete
jasem todo set 2 deadline tomorrow      # change a field
jasem track set 1 time 2h               # correct a duration
jasem acc rm 1                          # delete a record
```

---

## Core concepts

Everything is organised into **three symmetric namespaces** that share the same
verbs:

| Namespace | Tracks | Add example |
|-----------|--------|-------------|
| **`todo`** | tasks / to-dos | `jasem todo "submit report by friday, work"` |
| **`track`** | time spent | `jasem track "1h30min code review, work"` |
| **`acc`** | money spent | `jasem acc "50k lunch with the team, food"` |

Each namespace understands the same verbs:

```text
jasem <todo|track|acc> "<free text>"     add an entry  (AI-parsed)
jasem <todo|track|acc> list              view entries
jasem <todo|track|acc> tags              categories in use, with counts
jasem <todo|track|acc> set <id> …        edit one field of an entry
jasem <todo|track|acc> rm  <id> …        delete entries
jasem <track|acc>      report            aggregated totals & charts
```

Plus task-only views (`today`, `week`, `overdue`, `all`, `find`, `done`) and the
no-args [dashboard](#the-dashboard). `todo` also answers to `task` / `tasks`.

Every entry gets a stable numeric **id** (shown when you add it and in every
list); you address entries by that id when editing or deleting.

---

## Tasks

`jasem todo` is the task manager. You add tasks in plain language and jasem
extracts a **title**, **deadline**, **priority**, and **tags**; everything else
is for viewing, searching, completing, and editing them.

### Adding a task

Anything that isn't a known view or verb is treated as a new task description:

```text
$ jasem todo "pay rent next friday, high priority, finance"
✓ added #1: pay rent
  priority=high  deadline=2026-06-19  tags=finance

$ jasem todo "review Ali PR by tomorrow, work"
✓ added #2: review Ali PR
  priority=medium  deadline=2026-06-17  tags=work
```

* The **deadline** is read from natural language (see
  [Natural language input](#natural-language-input)).
* The **priority** is `high`, `medium` (default), or `low`.
* **Tags** are short topic words you mention (`work`, `finance`, `personal`).
* Commas are optional — they just help the parser.

**Force-adding text that starts with a command word.** If your task literally
starts with a word like `list`, `done`, `set`, or `rm`, jasem would treat it as a
verb. Use `add` to force it to be a new task:

```sh
jasem todo add "done the dishes tonight"     # adds a task titled "done the dishes"
jasem todo add "list everyone for the party" # adds a task, doesn't list
```

### Viewing tasks

A bare `jasem todo` shows open tasks, soonest deadline first. The columns are:
bullet, id, priority, **relative deadline**, title, tags, and **age** (how long
ago it was created).

| Command | Shows |
|---------|-------|
| `jasem todo` | open tasks (same as `list`) |
| `jasem todo list` *(alias `ls`)* | open tasks |
| `jasem todo today` | tasks due today |
| `jasem todo week` | tasks due within the next 7 days |
| `jasem todo overdue` | past deadline and not done — shown in **red** |
| `jasem todo all` | everything, including completed tasks |

**Filter a view by category** — append one or more categories to keep only tasks
that have **all** of them:

```sh
jasem todo list work             # open tasks tagged work
jasem todo list work urgent      # open tasks tagged BOTH work and urgent
jasem todo all finance           # all tasks (incl. done) tagged finance
```

**List categories** (counts cover open tasks only):

```text
$ jasem todo tags
Categories — open tasks
    3  #work
    1  #finance
    1  #health
```

### Searching

`find` (alias `search`) matches text in a task's **title or tags**,
case-insensitively:

```sh
jasem todo find rent
jasem todo find "ali pr"
```

### Completing tasks

Mark one or more tasks complete by id. Completed tasks disappear from open views
but remain in `jasem todo all`:

```text
$ jasem todo done 1
✓ completed: #1 pay rent

$ jasem todo done 2 3 5        # several at once
```

### Deleting tasks

Permanently remove tasks by id (`rm`, or `remove` / `del` / `delete`):

```text
$ jasem todo rm 4
✓ removed 1 task(s)
```

> Deletion is permanent. If you only want it out of your open list, use `done`
> instead — or recover the row from git or a backup of `~/.jasem/tasks.md`.

### Editing a field

`set` (alias `edit`) changes exactly one field of one task:

```sh
jasem todo set 3 priority high
jasem todo set 3 deadline next friday
jasem todo set 3 deadline 2026-07-01
jasem todo set 3 category work finance     # replaces the tag set
```

| Field | Aliases | Values |
|-------|---------|--------|
| `priority` | `prio`, `p` | `high` · `medium` · `low` |
| `deadline` | `due`, `date`, `d` | any date phrase, or a clear-word to remove it |
| `category` | `categories`, `tag`, `tags`, `c` | space/comma-separated tags, or a clear-word |

**Clearing a field** — to remove a deadline or all categories, set the value to
any of: `none`, `no`, `clear`, `remove`, `-`, `n/a`, `na`, `null`.

```sh
jasem todo set 3 deadline none      # task now has no deadline
jasem todo set 3 category clear     # task now has no tags
```

(`priority` can't be cleared — every task is `high`, `medium`, or `low`.)

---

## Time tracking

`jasem track` is a lightweight time log. You describe what you did in plain
language; jasem extracts a **duration**, a **work description**, a **date**, and
a **tag**.

### Logging time

```text
$ jasem track "1h45min debugging the parser yesterday, work"
✓ tracked #1 1h 45min · debugging the parser · 2026-06-16 · #work

$ jasem track "spent half an hour on emails"
✓ tracked #2 30min · on emails · today · #work
```

* **Duration** understands `2h`, `30 min`, `1h 30min`, `1h45min`, `half an
  hour`, `an hour and a half`, or a bare number (treated as minutes).
* **Date** defaults to today; say `yesterday`, `monday`, `june 18`, etc.
* **Tag** defaults to `work` when you don't mention one.
* Commas are optional. Logging prints the new entry's **id**.

> **If a duration can't be read**, jasem still saves the entry but warns you —
> it's stored as-is and **won't count toward totals** until you fix it with
> `jasem track set <id> time …`.

### Listing entries

```text
$ jasem track list
 Time entries ────────────────────────────────────
  1  2026-06-16  1h 45min  debugging the parser  #work
  2  2026-06-17  30min     on emails             #work
```

`list` accepts an optional **period** and an optional **tag** filter:

```sh
jasem track list                 # all entries (the default period)
jasem track list week            # last 7 days
jasem track list month           # last 30 days
jasem track list today           # just today
jasem track list week work       # last 7 days, only #work
```

**Periods:** `today` · `week` (last 7 days) · `month` (last 30 days) · `all`.
For `list`, the default is **`all`**.

**List categories:**

```text
$ jasem track tags
Categories — time
    5  #work
    2  #personal
```

### Reports

`report` aggregates a period into totals, a by-tag breakdown, a day-by-day
timeline, and your top activities — with a period-over-period trend:

```sh
jasem track report               # defaults to the last 7 days (week)
jasem track report month         # last 30 days
jasem track report week work     # last 7 days, only #work
```

Periods are the same as for `list`, but `report` **defaults to `week`**. The
trend compares the chosen window against the equally long window just before it
(an `all` report has no prior window, so no trend is shown).

### Correcting entries

`set` (alias `edit`) changes one field of one entry by id:

```sh
jasem track set 3 time 1h30min
jasem track set 3 work "reviewing the PR"
jasem track set 3 date yesterday
jasem track set 3 tag personal
```

| Field | Aliases | Notes |
|-------|---------|-------|
| `time` | `duration`, `dur`, `t` | re-parsed into a canonical `1h 30min` form |
| `work` | `desc`, `description`, `w` | the description text |
| `date` | `day`, `d` | any date phrase |
| `tag` | `category`, `categories`, `c` | a clear-word resets it to `work` |

Delete entries by id (`remove` / `del` / `delete` also work):

```text
$ jasem track rm 2 3 4
✓ removed 3 time entries
```

---

## Spending

`jasem acc` is a spending log ("acc" as in *accounting*). It extracts an
**amount**, a **title**, an optional longer **description**, a **date**, and a
**tag**.

### Recording spending

```text
$ jasem acc "50k lunch with the team yesterday, food"
✓ recorded #1 50,000 · lunch with the team · 2026-06-16 · #food

$ jasem acc "spent 1.5m on a new phone, the old one finally died"
✓ recorded #2 1,500,000 · a new phone · today · #general
  the old one finally died
```

* **Amount** understands `50000`, `50k` (50,000), `1.5m` (1,500,000), `1,200`,
  and bare numbers. The first number found in the text is used.
* **Date** defaults to today; **tag** defaults to `general`.
* A second clause often becomes the **description** (a longer note kept with the
  record), as in the phone example.
* Commas are optional. Recording prints the new entry's **id**.

> jasem is **currency-agnostic**: it stores and sums plain numbers and never
> assumes a currency symbol. Use whatever units you like (toman, dollars, cents)
> as long as you're consistent.

> **If an amount can't be read**, jasem still saves the record but warns you —
> it won't count toward totals until you fix it with `jasem acc set <id> amount …`.

### Listing records

```text
$ jasem acc list
 Spending ──────────────────────────────────────────
  1  2026-06-16     50,000  lunch with the team  #food
  2  2026-06-17  1,500,000  a new phone          #general
```

`list` accepts an optional **period** and **tag** filter, exactly like
`track list`:

```sh
jasem acc list                 # all records (the default period)
jasem acc list week            # last 7 days
jasem acc list month food      # last 30 days, only #food
```

**Periods:** `today` · `week` · `month` · `all` (default **`all`** for `list`).

**List categories:**

```text
$ jasem acc tags
Categories — spending
    4  #food
    2  #transport
    1  #rent
```

### Reports

```sh
jasem acc report               # defaults to the last 7 days (week)
jasem acc report month         # last 30 days
jasem acc report month food    # last 30 days, only #food
```

Totals, by-tag breakdown, timeline, top spends, and a period-over-period trend.
`report` **defaults to `week`**.

### Correcting records

`set` (alias `edit`) changes one field of one record by id:

```sh
jasem acc set 3 amount 60k
jasem acc set 3 title "dinner out"
jasem acc set 3 description "team celebration"
jasem acc set 3 date yesterday
jasem acc set 3 tag food
```

| Field | Aliases | Notes |
|-------|---------|-------|
| `amount` | `amt`, `cost`, `price`, `a` | re-parsed into a canonical `60,000` form |
| `title` | `text`, `name`, `t` | the short summary |
| `description` | `desc`, `note`, `notes`, `details` | longer note; a clear-word empties it |
| `date` | `day`, `d` | any date phrase |
| `tag` | `category`, `categories`, `c` | a clear-word resets it to `general` |

Delete records by id (`remove` / `del` / `delete` also work):

```text
$ jasem acc rm 2
✓ removed 1 spending record(s)
```

---

## The dashboard

Run **`jasem`** with no arguments for a one-screen home view that pulls together
all three namespaces — what needs attention today, plus the time you've tracked
and the money you've spent.

```sh
jasem
```

The dashboard is built **entirely from your local Markdown files** and renders
**fully offline** — it never calls a model. To drill into any part of it, use the
namespace commands:

```sh
jasem todo today          # everything due today
jasem todo overdue        # what's past its deadline
jasem track report week   # where your time went
jasem acc report month    # where your money went
```

---

## Natural language input

The thing that makes jasem fast is that you never fill in fields — you write a
sentence and jasem extracts the structure. There are two layers:

1. **The AI parser** ([AI backends](#ai-backends)) turns your free text into
   rough fields — a title, a date *phrase*, a priority, tags, an amount, etc.
2. **A built-in, offline resolver** then turns date phrases into real calendar
   dates and normalises durations and amounts. This layer is pure regex and
   always runs, so **even with no model reachable, dates/durations/amounts are
   still parsed** — you just lose the smarter title/tag splitting.

### Dates

The resolver tries these forms, in priority order:

| You write | Resolves to |
|-----------|-------------|
| `2026-07-01` (any `YYYY-MM-DD` in the text) | that exact date |
| `in 3 days`, `in 2 weeks`, `in 1 month` | offset from today |
| `next friday`, `next monday` … | the next such weekday (always in the future) |
| `tomorrow` | today + 1 |
| `yesterday` | today − 1 |
| `today`, `tonight`, `now` | today |
| `next week` | today + 7 |
| `next month` | one month ahead (day clamped to month length) |
| `eow`, `end of week`, `this week` | the coming Friday |
| `friday`, `mon`, `this tuesday` … | the next occurrence of that weekday — **today counts** if it matches |
| `june 20`, `20 june`, `june 20 2027` | that calendar date; **rolls to next year** if it has already passed and no year was given |

Weekday and month **names and common abbreviations** are recognised
(`mon`/`monday`, `jun`/`june`).

**"No date" words** — to mean *no deadline*, use any of: `none`, `no deadline`,
`no date`, `n/a`, `na`, `null`, `someday`, `-` (or just leave it out).

**How dates are displayed** — stored dates are absolute (`2026-07-01`) but shown
relative so lists stay scannable:

* **Deadlines:** `overdue`, `yesterday`, `today`, `tomorrow`, `in 4d`, then
  `in 2w` (up to ~10 weeks), then `in 3mo`.
* **Age** (when a task was created): `today`, `6d`, `3w`, `5mo`, `2y`.

### Durations (time tracking)

A duration is one or more *number + unit* pieces, summed:

| Unit | Spellings |
|------|-----------|
| hours | `h`, `hr`, `hrs`, `hour`, `hours` |
| minutes | `m`, `min`, `mins`, `minute`, `minutes` |

```text
2h            -> 120 min
30 min        -> 30 min
1h 30min      -> 90 min
1h45min       -> 105 min   (units can butt straight against the next number)
90            -> 90 min     (a bare number is read as minutes)
```

A unit only counts when it's really a unit — the `h` in "5 hamburgers" is
ignored. Durations are stored in a canonical `1h 30min` form.

### Amounts (spending)

The **first number** found in the text is taken as the amount:

| You write | Amount |
|-----------|--------|
| `50000` | 50,000 |
| `50k` | 50,000 |
| `1.5m` | 1,500,000 |
| `2b` | 2,000,000,000 |
| `1,200` | 1,200 (comma = thousands separator) |
| `paid 50k for lunch` | 50,000 |

Magnitude suffixes are `k` (thousand), `m` (million), `b` (billion). Amounts are
stored with thousands separators (`50,000`).

---

## AI backends

Parsing free text into fields is the **only** step in jasem that uses a model.
Everything else — listing, reporting, the dashboard, editing — is pure local
code. You pick a backend with `JASEM_PROVIDER`, and if no model is reachable
jasem still saves your entries using its built-in regex parsing.

| `JASEM_PROVIDER` | Backend | Needs a key? | Default model |
|------------------|---------|--------------|---------------|
| `ollama` *(default)* | Local [Ollama](https://ollama.com) | no | `qwen2.5:3b` |
| `openai` | Any OpenAI-compatible API | yes | `gpt-4o-mini` |
| `anthropic` | Anthropic (Claude) | yes | `claude-opus-4-8` |

Override the model for any provider with `JASEM_MODEL`.

### Ollama — local, free, private (default)

Nothing to configure beyond having Ollama running with a small model pulled:

```sh
ollama serve
ollama pull qwen2.5:3b
```

jasem talks to Ollama at `http://localhost:11434` by default; point elsewhere
with `OLLAMA_HOST`. Use any local model with `JASEM_MODEL=llama3.1:8b`.

### OpenAI-compatible APIs

Works with OpenAI and any compatible service (Groq, OpenRouter, LM Studio, vLLM):

```sh
export JASEM_PROVIDER=openai
export JASEM_API_KEY=sk-...
export JASEM_OPENAI_API_BASE=https://openrouter.ai/api/v1   # non-OpenAI hosts
export JASEM_MODEL=gpt-4o-mini
```

* **Base URL resolution:** `JASEM_OPENAI_API_BASE` → `JASEM_OPENAI_BASE_URL` →
  `OPENAI_BASE_URL` → `JASEM_API_BASE`. With none set, OpenAI's own endpoint.
* **API key resolution:** `JASEM_API_KEY` → `OPENAI_API_KEY` → `ANTHROPIC_API_KEY`.

For a local OpenAI server (e.g. LM Studio):

```sh
export JASEM_PROVIDER=openai
export JASEM_OPENAI_API_BASE=http://localhost:1234/v1
export JASEM_API_KEY=lm-studio          # any non-empty string
export JASEM_MODEL=your-local-model
```

### Anthropic (Claude)

```sh
export JASEM_PROVIDER=anthropic
export JASEM_API_KEY=sk-ant-...
export JASEM_MODEL=claude-opus-4-8       # optional; this is the default
```

### When the backend is down

jasem never loses an entry because a model is unavailable. If the backend is
unreachable or misconfigured:

* **Tasks** are saved with the raw text as the title and the date parsed by regex.
* **Time** and **spending** fall back to a simple comma format:
  `<duration/amount>, <description>[, <date>][, <tag>]`.

You'll see a short warning, but the add always succeeds — so you can use jasem
with no AI at all:

```sh
jasem track "1h30min, code review, yesterday, work"
jasem acc   "50k, lunch, yesterday, food"
```

`jasem help` prints the resolved provider, model, and file paths so you can
confirm what jasem will actually use.

---

## Configuration

jasem has **no config file** — everything is controlled by environment variables,
read once at startup. Set them in your shell profile (`~/.zshrc`, `~/.bashrc`).
Run `jasem help` to see what jasem resolved.

**Files & directories** (`~` is expanded):

| Variable | Default | Controls |
|----------|---------|----------|
| `JASEM_DIR` | `~/.jasem` | the data directory |
| `JASEM_FILE` | `<JASEM_DIR>/tasks.md` | the tasks file |
| `JASEM_TRACK_FILE` | `<JASEM_DIR>/timelog.md` | the time-log file |
| `JASEM_SPEND_FILE` | `<JASEM_DIR>/spending.md` | the spending file |

**AI provider:**

| Variable | Default | Controls |
|----------|---------|----------|
| `JASEM_PROVIDER` | `ollama` | `ollama` · `openai` · `anthropic` |
| `JASEM_MODEL` | per-provider | the model id |
| `JASEM_API_KEY` | — | API key for `openai`/`anthropic` |
| `JASEM_OPENAI_API_BASE` | — | base URL for OpenAI-compatible hosts |
| `JASEM_API_BASE` | — | generic base-URL fallback |
| `OLLAMA_HOST` | `http://localhost:11434` | the Ollama server |

(Fallbacks: API key → `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`; OpenAI base URL →
`JASEM_OPENAI_BASE_URL` / `OPENAI_BASE_URL` / `JASEM_API_BASE`.)

**Calendar & appearance:**

| Variable | Default | Controls |
|----------|---------|----------|
| `JASEM_JALALI` | unset (Gregorian) | `1`/`true`/`yes`/`on` → Persian calendar |
| `JASEM_ACCENT` | `cyan` | accent colour — a name (`magenta`, …) or `r,g,b` |
| `NO_COLOR` | unset | set to force plain, uncoloured output |
| `FORCE_COLOR` | unset | set to force colour even when output isn't a terminal |

**Sample profile block:**

```sh
# ~/.zshrc — jasem
export JASEM_DIR=~/Dropbox/jasem
export JASEM_PROVIDER=ollama
export JASEM_MODEL=qwen2.5:3b
export JASEM_ACCENT=cyan
# export JASEM_JALALI=true        # uncomment for the Persian calendar
```

---

## Persian (Jalali) calendar

jasem can work entirely in the Persian (Jalali / Shamsi) calendar:

```sh
export JASEM_JALALI=true        # also accepts 1 / yes / on
jasem todo "pay rent 1405-04-10, finance"   # type deadlines in Jalali
jasem todo list                              # dates are shown in Jalali
```

* Every date jasem **shows** is rendered in Jalali.
* Every explicit date you **type** is read as Jalali and converted before storage.
* **Your data on disk stays Gregorian ISO** (`YYYY-MM-DD`), so the same files work
  whether the flag is on or off — switch back and forth freely.

Relative phrases (`tomorrow`, `next friday`, `in 3 days`) are calendar-agnostic
and behave identically in both modes; only the displayed date and explicit numeric
dates you type are Jalali. Leave `JASEM_JALALI` unset (or `false`) for the default
Gregorian calendar.

---

## Data files and storage

jasem stores everything as plain **Markdown tables** in `~/.jasem/` (relocatable
via [Configuration](#configuration)). No database, no binary format — read, grep,
edit, diff, sync, and version-control your data with ordinary tools.

| File | Holds | Managed by |
|------|-------|------------|
| `~/.jasem/tasks.md` | tasks | `jasem todo` |
| `~/.jasem/timelog.md` | time entries | `jasem track` |
| `~/.jasem/spending.md` | spending records | `jasem acc` |

**`tasks.md`:**

```markdown
| ID | ✓ | Priority | Deadline | Task | Tags | Created |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | ☐ | high | 2026-06-19 | pay rent | finance | 2026-06-15 |
| 2 | ☑ | medium | - | call dentist | health | 2026-06-14 |
```

`✓` is `☐` (open) or `☑` (done); empty `Deadline`/`Tags` show as `-`.

**`timelog.md`:**

```markdown
| ID | Date | Time | Work | Tag |
| --- | --- | --- | --- | --- |
| 1 | 2026-06-16 | 1h 45min | debugging the parser | work |
```

**`spending.md`:**

```markdown
| ID | Date | Amount | Title | Description | Tag |
| --- | --- | --- | --- | --- | --- |
| 1 | 2026-06-16 | 50,000 | lunch with the team | - | food |
```

**Hand-editing** is fully supported. A few rules keep things safe:

* Keep the column order and the header rows intact.
* Every data row needs an **integer ID** in the first column; rows whose first
  cell isn't a number are silently skipped on load.
* Give hand-added rows unique ids — jasem assigns the next id as *(highest
  existing id) + 1*, so duplicates can collide.
* Avoid raw `|` inside a cell.

**Backup / sync / version control** — because it's all text in one directory:

```sh
cd ~/.jasem && git init && git add . && git commit -m "snapshot"   # version it
export JASEM_DIR=~/Dropbox/jasem                                   # or sync it
```

Since `rm` is permanent within jasem, a periodic `git commit` in `~/.jasem` is the
simplest safety net — you can recover a deleted row with `git checkout`.

---

## Command reference

A one-page cheat-sheet. For the same thing in your terminal, run `jasem help`.

**Top level**

```text
jasem                      the dashboard (no args) — offline summary
jasem help                 the full built-in reference   (-h, --help)
jasem version              the installed version          (-v, --version)
```

**Tasks — `jasem todo`** (also `task` / `tasks`)

```text
jasem todo "<text>"            add a task (deadline, priority, tags auto-detected)
jasem todo add "<text>"        force-add (text that starts with a command word)
jasem todo                     open tasks, soonest deadline first
jasem todo list [cat…]         same; filter by categories          (alias: ls)
jasem todo today               due today
jasem todo week                due within the next 7 days
jasem todo overdue             past deadline, not done (red)
jasem todo all [cat…]          everything, including completed
jasem todo tags                categories in use (open tasks), with counts
jasem todo find "<text>"       search titles & tags                 (alias: search)
jasem todo done <id>…          mark task(s) complete
jasem todo rm <id>…            delete task(s)         (remove, del, delete)
jasem todo set <id> <field> <value>                  edit one field  (alias: edit)
   fields: priority(prio,p) · deadline(due,date,d) · category(tag,tags,c)
```

**Time — `jasem track`**

```text
jasem track "<text>"                log time (duration, date & tag auto-detected)
jasem track list [period] [tag]     logged entries          (default period: all)
jasem track tags                    categories in use, with counts
jasem track report [period] [tag]   totals · by-tag · timeline · top activities
                                                            (default period: week)
jasem track rm <id>…                delete entries     (remove, del, delete)
jasem track set <id> <field> <value>                 edit one field  (alias: edit)
   fields: time(duration,dur,t) · work(desc,w) · date(day,d) · tag(category,c)
```

**Spending — `jasem acc`**

```text
jasem acc "<text>"                  record spending (amount, date & tag detected)
jasem acc list [period] [tag]       recorded spending       (default period: all)
jasem acc tags                      categories in use, with counts
jasem acc report [period] [tag]     totals · by-tag · timeline · top spends
                                                            (default period: week)
jasem acc rm <id>…                  delete record(s)   (remove, del, delete)
jasem acc set <id> <field> <value>                   edit one field  (alias: edit)
   fields: amount(amt,cost,price,a) · title(name,t) · description(desc,note) ·
           date(day,d) · tag(category,c)
```

**Periods** (for `list` / `report`): `today` · `week` (7d) · `month` (30d) ·
`all`. `list` defaults to **all**, `report` to **week**.

**Clear-words** (to empty a field): `none` · `no` · `clear` · `remove` · `-` ·
`n/a` · `na` · `null`.

---

## FAQ and troubleshooting

**Do I need an AI model or internet?** No. A model only improves the first pass of
parsing free text; with none reachable, entries are still saved by regex, and
every other feature is fully offline.

**`jasem: command not found`.** The script isn't on your `PATH`. With pipx, run
`pipx ensurepath` and open a new shell; with `pip install --user`, add your
user-base bin directory (e.g. `~/.local/bin`) to `PATH`.

**My deadline/duration/amount didn't parse.** Check the confirmation line jasem
prints after adding. If a duration/amount couldn't be read, fix it with
`jasem track set <id> time …` / `jasem acc set <id> amount …`. For dates, check
the phrase against the [Natural language input](#natural-language-input) table, or
type an explicit `YYYY-MM-DD`. With no model running, add commas:
`jasem track "1h30min, code review, yesterday, work"`.

**"Couldn't parse with the … backend" warnings.** The model wasn't reachable, so
jasem fell back to local parsing (the entry was still saved). Start your backend
(`ollama serve`) or fix the provider settings — `jasem help` shows what it
resolved.

**My task starts with a word like "list" or "done".** Force it with `add` (tasks)
or by quoting (track/acc): `jasem todo add "done the dishes tonight"`.

**I deleted something by accident.** `rm` is permanent within jasem, but your data
is plain text — recover the row from git or a backup of `~/.jasem/`. A periodic
`git commit` there is the simplest safety net.

**What's the difference between `done` and `rm`?** `done` marks a task complete
(it leaves the open views but stays in `jasem todo all`); `rm` deletes it
permanently. Time and spending entries have no "done" — correct them with `set` or
delete with `rm`.

**What currency does `jasem acc` use?** None — it sums plain numbers. Pick a unit
and stay consistent.

**Which version do I have?** `jasem version`.

---

## License

jasem is MIT-licensed. Source and issues:
<https://github.com/mrfatolahi1/jasem>.
