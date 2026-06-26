# Dashboard

Run **`jasem`** with no arguments for a one-screen home view that pulls together
all three namespaces — what needs attention today, plus the time you've tracked
and the money you've spent.

```sh
jasem
```

The dashboard is built **entirely from your local Markdown files** and renders
**fully offline** — it never calls a model. It's the fastest way to answer "what
should I be doing, and where did my time and money go?"

## What it draws from

| Source file | Feeds |
|-------------|-------|
| `~/.jasem/tasks.md` | tasks due today, overdue, and upcoming |
| `~/.jasem/timelog.md` | time tracked |
| `~/.jasem/spending.md` | money spent |

(See [[Configuration]] to relocate these files and [[Data Files]] for the
format.)

## Reading it

Lists and reports throughout jasem render as aligned, width-aware tables with bar
charts and sparklines, and the dashboard is the densest example — it adapts to
your terminal width. Colour is automatic on a terminal; set `NO_COLOR` to force
plain text or `JASEM_ACCENT` to recolour the accent (see [[Configuration]]).

## Going deeper

The dashboard is a summary. To drill into any part of it, use the namespace
commands:

```sh
jasem todo today          # everything due today
jasem todo overdue        # what's past its deadline
jasem track report week   # where your time went
jasem acc report month    # where your money went
```

## See also

* [[Tasks]] · [[Time Tracking]] · [[Spending]]
* [[Command Reference]]
