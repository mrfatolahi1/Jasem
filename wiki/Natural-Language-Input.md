# Natural Language Input

The thing that makes jasem fast is that you never fill in fields — you write a
sentence and jasem extracts the structure. This page documents exactly what it
understands for **dates**, **durations**, and **amounts**.

There are two layers:

1. **The AI parser** (see [[AI Backends]]) turns your free text into rough fields
   — a title, a date *phrase*, a priority, tags, an amount, and so on.
2. **A built-in, offline resolver** then turns date phrases into real calendar
   dates and normalises durations and amounts. This layer is pure regex and
   always runs, so **even with no model reachable, dates/durations/amounts are
   still parsed** — you just lose the smarter title/tag splitting.

## Dates

Dates are accepted when adding any entry and anywhere a `deadline`/`date` field
is set. The resolver tries these forms, in priority order:

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
| `june 20`, `20 june`, `june 20 2027` | that calendar date; **rolls to next year** if the date has already passed and no year was given |

Weekday and month **names and common abbreviations** are recognised
(`mon`/`monday`, `jun`/`june`).

### "No date" words

To mean *no deadline*, use any of: `none`, `no deadline`, `no date`, `n/a`,
`na`, `null`, `someday`, `-` (or just leave it out). These also clear a deadline
when editing: `jasem todo set 3 deadline none`.

### How dates are displayed

Stored dates are absolute (`2026-07-01`) but **shown relative** so lists stay
scannable:

* **Deadlines:** `overdue`, `yesterday`, `today`, `tomorrow`, `in 4d`, then
  `in 2w` (up to ~10 weeks), then `in 3mo`.
* **Age** (when a task was created): `today`, `6d`, `3w`, `5mo`, `2y`.

## Durations (time tracking)

Used by `jasem track`. A duration is one or more *number + unit* pieces, summed:

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
ignored. When a model is in play, phrases like `half an hour` (30) and `an hour
and a half` (90) are understood too; the offline fallback handles the numeric
forms above.

Durations are stored in a canonical `1h 30min` form. If jasem can't find a
duration at all, it saves your text as-is and warns that the entry **won't count
toward totals** until you fix it with `jasem track set <id> time …`.

## Amounts (spending)

Used by `jasem acc`. The **first number** found in the text is taken as the
amount:

| You write | Amount |
|-----------|--------|
| `50000` | 50,000 |
| `50k` | 50,000 |
| `1.5m` | 1,500,000 |
| `2b` | 2,000,000,000 |
| `1,200` | 1,200 (comma = thousands separator) |
| `paid 50k for lunch` | 50,000 |

Magnitude suffixes are `k` (thousand), `m` (million), `b` (billion). Amounts are
stored with thousands separators (`50,000`). If no number is found, the record is
saved as-is and won't count toward totals until you fix it with
`jasem acc set <id> amount …`.

jasem never assumes a currency — it sums plain numbers. Pick a unit and stay
consistent.

## Quoting and the parser

* **Always quote** a free-text description. It keeps multi-word text together and
  keeps shell characters (`& ! * ( )`) literal.
* The parser captures temporal words even after `by`/`due` ("submit report **by
  friday**") and pulls the duration/amount/tags **out** of the title, so the
  stored title stays clean.
* If your text starts with a command word (`list`, `done`, `set`, `rm`, …), see
  the force-add note on the [[Tasks]], [[Time Tracking]], and [[Spending]] pages.

## See also

* [[AI Backends]] — choosing and configuring the model that does the first pass
* [[Jalali Calendar]] — typing and showing dates in the Persian calendar
