# Spending (`jasem acc`)

`jasem acc` is a spending log ("acc" as in *accounting*). You describe a purchase
in plain language; jasem extracts an **amount**, a **title**, an optional longer
**description**, a **date**, and a **tag**, then lets you list and report on it.

## Recording spending

Any text that isn't a known verb is recorded as a new entry:

```text
$ jasem acc "50k lunch with the team yesterday, food"
✓ recorded #1 50,000 · lunch with the team · 2026-06-16 · #food

$ jasem acc "spent 1.5m on a new phone, the old one finally died"
✓ recorded #2 1,500,000 · a new phone · today · #general
  the old one finally died
```

* **Amount** understands `50000`, `50k` (50,000), `1.5m` (1,500,000), `1,200`,
  and bare numbers. The first number found in the text is used, so `paid 50k`
  reads as 50,000.
* **Date** defaults to today; say `yesterday`, `monday`, `june 18`, etc.
* **Tag** defaults to `general` when you don't mention one.
* A second clause often becomes the **description** (a longer note kept with the
  record), as in the phone example above.
* Commas are optional. Recording prints the new entry's **id**.

See [[Natural Language Input]] for the amount and date grammar.

> **If an amount can't be read**, jasem still saves the record but warns you —
> it's stored as-is and **won't count toward totals** until you fix it with
> `jasem acc set <id> amount …`.

> jasem is currency-agnostic: it stores and sums plain numbers and never assumes
> a currency symbol. Use whatever units you like (toman, dollars, cents) as long
> as you're consistent.

## Listing records

```text
$ jasem acc list
 Spending ──────────────────────────────────────────
  1  2026-06-16     50,000  lunch with the team  #food
  2  2026-06-17  1,500,000  a new phone          #general
```

`list` accepts an optional **period** and an optional **tag** filter:

```sh
jasem acc list                 # all records (the default period)
jasem acc list week            # last 7 days
jasem acc list month           # last 30 days
jasem acc list today           # just today
jasem acc list month food      # last 30 days, only #food
jasem acc list all rent        # everything tagged rent
```

**Periods:** `today` · `week` (last 7 days) · `month` (last 30 days) · `all`.
For `list`, the default is **`all`**.

## Listing categories

```text
$ jasem acc tags
Categories — spending
    4  #food
    2  #transport
    1  #rent
```

## Reports

`report` aggregates a period into totals, a by-tag breakdown, a timeline, and
your top spends — with a period-over-period trend:

```sh
jasem acc report               # defaults to the last 7 days (week)
jasem acc report month         # last 30 days
jasem acc report today
jasem acc report all
jasem acc report month food    # last 30 days, only #food
```

**Periods** are the same as for `list`, but `report` **defaults to `week`**. The
trend compares the chosen window against the equally long window just before it.

## Correcting records

### Edit a field

`set` (alias `edit`) changes one field of one record by id:

```sh
jasem acc set 3 amount 60k
jasem acc set 3 title "dinner out"
jasem acc set 3 description "team celebration"
jasem acc set 3 date yesterday
jasem acc set 3 tag food
```

**Fields and accepted aliases:**

| Field | Aliases | Notes |
|-------|---------|-------|
| `amount` | `amt`, `cost`, `price`, `a` | re-parsed into a canonical `60,000` form |
| `title` | `text`, `name`, `t` | the short summary |
| `description` | `desc`, `note`, `notes`, `details` | longer note; a clear-word empties it |
| `date` | `day`, `d` | any date phrase |
| `tag` | `category`, `categories`, `c` | a clear-word resets it to `general` |

A clear-word (`none`, `clear`, `-`, …) empties the `description`, and resets the
`tag` back to the default `general`.

### Delete records

```text
$ jasem acc rm 2
✓ removed 1 spending record(s)

$ jasem acc rm 2 3 4         # several at once
```

(`remove`, `del`, `delete` all work too.)

## Force-recording text that starts with a verb

If your purchase description literally starts with `list`, `set`, `rm`, `tags`,
or `report`, quote it so it's treated as a new record rather than a command.

## Where spending is stored

Records live in `~/.jasem/spending.md` as a hand-editable Markdown table — see
[[Data Files]].

## See also

* [[Natural Language Input]] — amount and date parsing in detail
* [[Time Tracking]] — the parallel `jasem track` namespace works the same way
* [[Command Reference]] — the cheat-sheet
