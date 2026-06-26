# Tasks (`jasem todo`)

`jasem todo` is the task manager. You add tasks in plain language and jasem
extracts a **title**, **deadline**, **priority**, and **tags**; everything else
is for viewing, searching, completing, and editing them.

> `task` and `tasks` are accepted as aliases for `todo`, so
> `jasem task "…"` works too.

## Adding a task

Anything that isn't a known view or verb is treated as a new task description:

```text
$ jasem todo "pay rent next friday, high priority, finance"
✓ added #1: pay rent
  priority=high  deadline=2026-06-19  tags=finance

$ jasem todo "review Ali PR by tomorrow, work"
✓ added #2: review Ali PR
  priority=medium  deadline=2026-06-17  tags=work
```

* The **deadline** is read from natural language — `next friday`, `tomorrow`,
  `in 3 days`, `june 20`, `2026-07-01`, … (see [[Natural Language Input]]).
* The **priority** is `high`, `medium` (default), or `low`.
* **Tags** are short topic words you mention (`work`, `finance`, `personal`).
* Commas are optional — they just help the parser.

### Force-adding text that starts with a command word

If your task literally starts with a word like `list`, `done`, `set`, or `rm`,
jasem would treat it as a verb. Use `add` to force it to be a new task:

```sh
jasem todo add "done the dishes tonight"     # adds a task titled "done the dishes"
jasem todo add "list everyone for the party" # adds a task, doesn't list
```

Quoting also keeps shell metacharacters (`& ! * ( )`) literal.

## Viewing tasks

A bare `jasem todo` shows open tasks, soonest deadline first:

```text
$ jasem todo
 Open tasks ──────────────────────────────────────────────
 ●  1  ⚑ high  in 4d  pay rent      #finance  today
 ●  2    med   today  call dentist  #health   2d
 ──────────────────────────── 2 open  ·  1 due today
```

The columns are: bullet, id, priority, **relative deadline**, title, tags, and
**age** (how long ago it was created). Deadlines render as `today`, `tomorrow`,
`in 4d`, `in 2w`, `overdue`, etc.

| Command | Shows |
|---------|-------|
| `jasem todo` | open tasks (same as `list`) |
| `jasem todo list` *(alias `ls`)* | open tasks |
| `jasem todo today` | tasks due today |
| `jasem todo week` | tasks due within the next 7 days |
| `jasem todo overdue` | past deadline and not done — shown in **red** |
| `jasem todo all` | everything, including completed tasks |

### Filtering a view by category

Append one or more categories to a list view to keep only tasks that have **all**
of them:

```sh
jasem todo list work             # open tasks tagged work
jasem todo list work urgent      # open tasks tagged BOTH work and urgent
jasem todo all finance           # all tasks (incl. done) tagged finance
```

### Listing categories

```text
$ jasem todo tags
Categories — open tasks
    3  #work
    1  #finance
    1  #health
```

Counts cover **open** tasks only.

## Searching

`find` (alias `search`) matches text in a task's **title or tags**,
case-insensitively:

```sh
jasem todo find rent
jasem todo find "ali pr"
```

## Completing tasks

Mark one or more tasks complete by id (ids come from any list):

```text
$ jasem todo done 1
✓ completed: #1 pay rent

$ jasem todo done 2 3 5        # several at once
```

Completed tasks disappear from the open views but remain in `jasem todo all`.

## Deleting tasks

Permanently remove tasks by id (`rm`, or the aliases `remove`/`del`/`delete`):

```text
$ jasem todo rm 4
✓ removed 1 task(s)

$ jasem todo rm 4 5 6
```

> Deletion is permanent. If you only want it out of your open list, use `done`
> instead — or, because everything is plain text, recover the row from git or a
> backup of `~/.jasem/tasks.md`.

## Editing a field

`set` (alias `edit`) changes exactly one field of one task:

```sh
jasem todo set 3 priority high
jasem todo set 3 deadline next friday
jasem todo set 3 deadline 2026-07-01
jasem todo set 3 category work finance     # replaces the tag set
```

**Fields and accepted aliases:**

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

## Where tasks are stored

Tasks live in `~/.jasem/tasks.md` as a Markdown table you can hand-edit. See
[[Data Files]] for the exact column layout.

## See also

* [[Natural Language Input]] — every date phrase jasem understands
* [[Command Reference]] — the one-page cheat-sheet
* [[Time Tracking]] and [[Spending]] — the sibling namespaces
