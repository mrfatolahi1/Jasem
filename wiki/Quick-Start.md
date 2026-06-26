# Quick Start

This page walks through the whole loop in a few minutes. If you haven't installed
jasem yet, see [[Installation]].

## 1. Add a task in plain language

Just describe it. jasem pulls out the title, deadline, priority, and tags:

```text
$ jasem todo "pay rent next friday, high priority, finance"
✓ added #1: pay rent
  priority=high  deadline=2026-06-19  tags=finance
```

Notice you didn't fill in any fields — `next friday` became a date, `high
priority` set the priority, and `finance` became a tag. See
[[Natural Language Input]] for everything jasem understands.

> **Tip:** Quote the whole description. It keeps shell characters like `&`, `!`,
> `*`, `(`, `)` literal and keeps multi-word text together.

## 2. See what's open

A bare `jasem todo` lists open tasks, soonest deadline first:

```text
$ jasem todo
 Open tasks ──────────────────────────────────────────────
 ●  1  ⚑ high  in 4d  pay rent      #finance  today
 ●  2    med   today  call dentist  #health   2d
 ──────────────────────────── 2 open  ·  1 due today
```

Deadlines show as relative time (`in 4d`, `today`, `overdue`); the last column is
each task's age. Other views: `today`, `week`, `overdue`, `all`. Full details on
the [[Tasks]] page.

## 3. Track some time

```text
$ jasem track "1h30min code review, work"
✓ tracked #1 1h 30min · code review · today · #work
```

Review it later:

```sh
jasem track list            # the entries
jasem track report week     # per-day totals, by-tag, top activities
```

See [[Time Tracking]].

## 4. Log spending

```text
$ jasem acc "50k lunch with the team, food"
✓ recorded #1 50,000 · lunch with the team · today · #food
```

```sh
jasem acc list              # the records
jasem acc report month      # totals for the last 30 days
```

See [[Spending]].

## 5. Get the big picture

Run `jasem` with no arguments for a one-screen [[Dashboard]] — what needs
attention today plus the time and money you've logged, drawn straight from your
files and rendered fully offline.

```sh
jasem
```

## 6. Fix things

Everything is editable by id. The id is shown when you add an entry and in every
list.

```sh
jasem todo done 1                       # mark task #1 complete
jasem todo set 2 deadline tomorrow      # change a field
jasem track set 1 time 2h               # correct a duration
jasem acc rm 1                          # delete a record
```

## The mental model

Three namespaces, the same verbs everywhere:

```text
jasem <todo|track|acc> "<free text>"     add an entry  (AI-parsed)
jasem <todo|track|acc> list              view entries
jasem <todo|track|acc> tags              categories in use, with counts
jasem <todo|track|acc> set <id> …        edit one field of an entry
jasem <todo|track|acc> rm  <id> …        delete entries
jasem <track|acc>      report            aggregated totals & charts
```

Plus task-only views (`today`, `week`, `overdue`, `all`, `find`, `done`) and the
no-args dashboard. The whole thing is on one screen: run `jasem help`.

Next: pick a namespace — [[Tasks]], [[Time Tracking]], [[Spending]] — or wire up
a model in [[AI Backends]].
