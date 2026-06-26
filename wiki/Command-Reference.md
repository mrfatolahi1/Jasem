# Command Reference

A one-page cheat-sheet of every jasem command. For the same thing inside your
terminal, run **`jasem help`**.

## Top level

```text
jasem                      the dashboard (no args) — offline summary
jasem help                 the full built-in reference   (-h, --help)
jasem version              the installed version          (-v, --version)
jasem <todo|track|acc> …   the three namespaces (below)
```

`todo` also answers to `task` and `tasks`.

## Tasks — `jasem todo`

```text
jasem todo "<text>"            add a task (deadline, priority, tags auto-detected)
jasem todo add "<text>"        force-add (text that starts with a command word)

jasem todo                     open tasks, soonest deadline first
jasem todo list [cat…]         same; filter by one or more categories  (alias: ls)
jasem todo today               due today
jasem todo week                due within the next 7 days
jasem todo overdue             past deadline, not done (red)
jasem todo all [cat…]          everything, including completed
jasem todo tags                categories in use (open tasks), with counts
jasem todo find "<text>"       search titles & tags          (alias: search)

jasem todo done <id>…          mark task(s) complete
jasem todo rm <id>…            delete task(s)        (aliases: remove, del, delete)
jasem todo set <id> <field> <value>                 edit one field   (alias: edit)
```

**`set` fields:** `priority` (`prio`,`p`) → high·medium·low ·
`deadline` (`due`,`date`,`d`) → a date phrase or a clear-word ·
`category` (`tag`,`tags`,`c`) → space/comma tags or a clear-word.

```text
jasem todo set 3 priority high
jasem todo set 3 deadline next friday
jasem todo set 3 deadline none           # clear it
jasem todo set 3 category work finance   # replace tags
```

## Time — `jasem track`

```text
jasem track "<text>"          log time (duration, date & tag auto-detected)

jasem track list [period] [tag]     logged entries        (default period: all)
jasem track tags                    categories in use, with counts
jasem track report [period] [tag]   totals · by-tag · timeline · top activities
                                                          (default period: week)
jasem track rm <id>…                delete entries   (remove, del, delete)
jasem track set <id> <field> <value>                edit one field   (alias: edit)
```

**`set` fields:** `time` (`duration`,`dur`,`t`) · `work` (`desc`,`description`,`w`)
· `date` (`day`,`d`) · `tag` (`category`,`c`).

```text
jasem track set 3 time 1h30min
jasem track set 3 work "reviewing the PR"
jasem track set 3 date yesterday
jasem track set 3 tag personal
```

## Spending — `jasem acc`

```text
jasem acc "<text>"            record spending (amount, date & tag auto-detected)

jasem acc list [period] [tag]       recorded spending     (default period: all)
jasem acc tags                      categories in use, with counts
jasem acc report [period] [tag]     totals · by-tag · timeline · top spends
                                                          (default period: week)
jasem acc rm <id>…                  delete record(s)  (remove, del, delete)
jasem acc set <id> <field> <value>                  edit one field   (alias: edit)
```

**`set` fields:** `amount` (`amt`,`cost`,`price`,`a`) · `title` (`name`,`t`) ·
`description` (`desc`,`note`,`details`) · `date` (`day`,`d`) · `tag`
(`category`,`c`).

```text
jasem acc set 3 amount 60k
jasem acc set 3 title "dinner out"
jasem acc set 3 description "team celebration"
jasem acc set 3 date yesterday
jasem acc set 3 tag food
```

## Periods (for `list` / `report`)

```text
today    just today
week     last 7 days
month    last 30 days
all      everything (anchored at your earliest entry)
```

`list` defaults to **all**, `report` defaults to **week**.

## Clear-words (to empty a field)

`none` · `no` · `clear` · `remove` · `-` · `n/a` · `na` · `null`
(deadline/category clear; `track` tag → `work`; `acc` tag → `general`;
`acc` description → empty).

## Date phrases (a sampler)

```text
today · tomorrow · yesterday · next friday · in 3 days · in 2 weeks ·
next week · next month · eow / end of week · june 20 · 2026-07-01 · none
```

Full grammar: [[Natural Language Input]].

## Key environment variables

```text
JASEM_PROVIDER   ollama (default) · openai · anthropic
JASEM_MODEL      model id
JASEM_API_KEY    key for openai / anthropic
JASEM_DIR        data directory (default ~/.jasem)
JASEM_JALALI     true → Persian calendar
JASEM_ACCENT     accent colour name or r,g,b
NO_COLOR         force plain text
```

Full list: [[Configuration]].
