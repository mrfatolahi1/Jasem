# Time Tracking (`jasem track`)

`jasem track` is a lightweight time log. You describe what you did in plain
language; jasem extracts a **duration**, a **work description**, a **date**, and
a **tag**, then lets you list and report on it.

## Logging time

Any text that isn't a known verb is logged as a new entry:

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

See [[Natural Language Input]] for the full duration and date grammar.

> **If a duration can't be read**, jasem still saves the entry but warns you —
> it's stored as-is and **won't count toward totals** until you fix it with
> `jasem track set <id> time …`.

## Listing entries

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
jasem track list all personal    # everything tagged personal
```

**Periods:** `today` · `week` (last 7 days) · `month` (last 30 days) · `all`.
For `list`, the default is **`all`**.

## Listing categories

```text
$ jasem track tags
Categories — time
    5  #work
    2  #personal
```

## Reports

`report` aggregates a period into totals, a by-tag breakdown, a day-by-day
timeline, and your top activities — with a period-over-period trend:

```sh
jasem track report               # defaults to the last 7 days (week)
jasem track report month         # last 30 days
jasem track report today
jasem track report all
jasem track report week work     # last 7 days, only #work
```

**Periods** are the same as for `list`, but `report` **defaults to `week`**. The
trend compares the chosen window against the equally long window just before it
(an `all` report has no prior window, so no trend is shown).

## Correcting entries

### Edit a field

`set` (alias `edit`) changes one field of one entry by id:

```sh
jasem track set 3 time 1h30min
jasem track set 3 work "reviewing the PR"
jasem track set 3 date yesterday
jasem track set 3 tag personal
```

**Fields and accepted aliases:**

| Field | Aliases | Notes |
|-------|---------|-------|
| `time` | `duration`, `dur`, `t` | re-parsed into a canonical `1h 30min` form |
| `work` | `desc`, `description`, `w` | the description text |
| `date` | `day`, `d` | any date phrase |
| `tag` | `category`, `categories`, `c` | a clear-word resets it to `work` |

Resetting the tag to a clear-word (`none`, `clear`, `-`, …) sets it back to the
default `work`.

### Delete entries

```text
$ jasem track rm 2
✓ removed 1 time entry

$ jasem track rm 2 3 4         # several at once
```

(`remove`, `del`, `delete` all work too.)

## Force-logging text that starts with a verb

If what you did literally starts with `list`, `set`, `rm`, `tags`, or `report`,
quote it so it's treated as a new entry rather than a command — e.g.
`jasem track "rm old branches, 20min, work"` logs work; it does not delete.

## Where time is stored

Entries live in `~/.jasem/timelog.md` as a hand-editable Markdown table — see
[[Data Files]].

## See also

* [[Natural Language Input]] — duration and date parsing in detail
* [[Spending]] — the parallel `jasem acc` namespace works the same way
* [[Command Reference]] — the cheat-sheet
