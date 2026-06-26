# FAQ & Troubleshooting

## Do I need an AI model or an internet connection?

No. A model only improves the *first pass* of parsing free text. With no model
reachable, entries are still saved using built-in regex parsing, and every other
feature — lists, reports, the [[Dashboard]], editing — is fully offline. See
[[AI Backends]] and [[Natural Language Input]].

## `jasem: command not found`

The script isn't on your `PATH`. If you used pipx, run `pipx ensurepath` and open
a new shell. If you used `pip install --user`, add your user-base bin directory
(e.g. `~/.local/bin`) to `PATH`. See [[Installation]].

## My deadline/duration/amount didn't get parsed

* Confirm what jasem extracted from the confirmation line it prints after adding.
* If a **duration** or **amount** couldn't be read, jasem warns you and stores
  the text as-is — it **won't count toward totals** until you fix it:
  `jasem track set <id> time 1h30min` / `jasem acc set <id> amount 50k`.
* For dates, check the phrase against the table in [[Natural Language Input]].
  When in doubt, type an explicit `YYYY-MM-DD`.
* No model running? Add a bit of structure with commas:
  `jasem track "1h30min, code review, yesterday, work"`.

## "Couldn't parse with the … backend" warnings

The configured model wasn't reachable, so jasem fell back to local parsing (the
entry was still saved). Either start your backend (`ollama serve`) or fix the
provider settings — run `jasem help` to see the provider, model, and key jasem
resolved. Details: [[AI Backends]].

## My task starts with a word like "list" or "done"

That word is read as a command. Force it to be an entry with `add` (tasks) or by
quoting (track/acc):

```sh
jasem todo add "done the dishes tonight"
jasem track "rm old branches, 20min, work"
```

See the force-add notes on [[Tasks]], [[Time Tracking]], and [[Spending]].

## I deleted something by accident

`rm` is permanent within jasem. But your data is plain text in `~/.jasem/`, so if
you version-control or back up that directory you can recover the row from git or
a backup. A periodic `git commit` in `~/.jasem` is the simplest safety net — see
[[Data Files]].

## How do I change where my data lives?

Set `JASEM_DIR` (or the per-file `JASEM_FILE` / `JASEM_TRACK_FILE` /
`JASEM_SPEND_FILE`). Point it at a synced or version-controlled folder to back up
or share. See [[Configuration]].

## Can I edit the Markdown files directly?

Yes — keep the column order and give each row an integer id. jasem reads your
changes on the next command. See [[Data Files]].

## How do I work in the Persian (Jalali) calendar?

`export JASEM_JALALI=true`. Dates are shown and typed in Jalali while staying
Gregorian on disk. See [[Jalali Calendar]].

## The output has no colour / too much colour

Colour is automatic on a terminal. Set `NO_COLOR` to force plain text, or
`FORCE_COLOR` to keep colour when piping. Recolour the accent with
`JASEM_ACCENT`. See [[Configuration]].

## What's the difference between `done` and `rm`?

`done` marks a task complete — it leaves the open views but stays in
`jasem todo all`. `rm` deletes it permanently. There is no "done" for time or
spending entries; correct them with `set` or delete with `rm`.

## What currency does `jasem acc` use?

None — it sums plain numbers and never assumes a symbol. Pick a unit (toman,
dollars, cents) and stay consistent. See [[Spending]].

## Which version do I have?

```sh
jasem version
```

## See also

* [[Command Reference]] — every command at a glance
* [[Home]] — the wiki index
