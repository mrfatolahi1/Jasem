# Data Files & Storage

jasem stores everything as plain **Markdown tables** in `~/.jasem/` (relocatable
via [[Configuration]]). There's no database and no binary format — you can read,
grep, edit, diff, sync, and version-control your data with ordinary tools.

| File | Holds | Managed by |
|------|-------|------------|
| `~/.jasem/tasks.md` | tasks | `jasem todo` |
| `~/.jasem/timelog.md` | time entries | `jasem track` |
| `~/.jasem/spending.md` | spending records | `jasem acc` |

Each file is created automatically the first time you add to it.

## File formats

### `tasks.md`

```markdown
# Tasks

_Managed by the `jasem` CLI. You can hand-edit rows, but keep the column order._

| ID | ✓ | Priority | Deadline | Task | Tags | Created |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | ☐ | high | 2026-06-19 | pay rent | finance | 2026-06-15 |
| 2 | ☑ | medium | - | call dentist | health | 2026-06-14 |
```

* **✓** is `☐` (open) or `☑` (done).
* **Priority** is `high` / `medium` / `low`.
* **Deadline**, **Tags** use `-` when empty.
* **Dates** are always Gregorian `YYYY-MM-DD`, even in [[Jalali Calendar]] mode.

### `timelog.md`

```markdown
# Time log

_Managed by the `jasem track` CLI. Hand-edit rows freely, but keep the column order._

| ID | Date | Time | Work | Tag |
| --- | --- | --- | --- | --- |
| 1 | 2026-06-16 | 1h 45min | debugging the parser | work |
| 2 | 2026-06-17 | 30min | on emails | work |
```

The **Time** column is free-form text; anything jasem can parse as a duration
(`1h 30min`, `90`, `2h`) counts toward totals.

### `spending.md`

```markdown
# Spending log

_Managed by the `jasem acc` CLI. Hand-edit rows freely, but keep the column order._

| ID | Date | Amount | Title | Description | Tag |
| --- | --- | --- | --- | --- | --- |
| 1 | 2026-06-16 | 50,000 | lunch with the team | - | food |
| 2 | 2026-06-17 | 1,500,000 | a new phone | the old one finally died | general |
```

## Hand-editing

Editing by hand is fully supported — that's the point of plain text. A few rules
keep things safe:

* **Keep the column order** and the header rows intact.
* Every data row needs an **integer ID** in the first column; rows whose first
  cell isn't a number are silently skipped on load.
* New rows you add by hand don't need to be sorted — jasem sorts views itself.
* If you add rows manually, give them unique ids. jasem assigns the next id as
  *(highest existing id) + 1*, so duplicates can collide.
* Pipe characters in your text are handled by jasem on save; if you hand-edit,
  avoid raw `|` inside a cell.

After editing, just run a normal command (`jasem todo`, `jasem track list`, …)
and your changes are picked up immediately.

## Backup, sync & version control

Because it's all text in one directory, any of these just work:

```sh
# Version-control your data
cd ~/.jasem && git init && git add . && git commit -m "snapshot"

# Or keep it in a synced folder
export JASEM_DIR=~/Dropbox/jasem
```

Git is especially nice here: every `jasem` change becomes a readable diff, and
you can recover a deleted row with `git checkout`/`git show`. Since `rm` is
permanent within jasem, a periodic commit is the simplest safety net.

## See also

* [[Configuration]] — relocating the directory and individual files
* [[Jalali Calendar]] — why stored dates stay Gregorian
