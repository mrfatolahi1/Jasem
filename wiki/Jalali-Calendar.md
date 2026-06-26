# Jalali (Persian) Calendar

jasem can work entirely in the Persian (Jalali / Shamsi) calendar. Turn it on by
setting `JASEM_JALALI`:

```sh
export JASEM_JALALI=true        # also accepts 1 / yes / on
```

With the flag on:

```sh
jasem todo "pay rent 1405-04-10, finance"   # type deadlines in Jalali
jasem todo list                              # dates are shown in Jalali
```

## How it works

* Every date jasem **shows** is rendered in Jalali.
* Every explicit date you **type** (e.g. `1405-04-10`) is read as Jalali and
  converted before storage.
* **Your data on disk stays Gregorian ISO** (`YYYY-MM-DD`). The flag only changes
  input interpretation and display — so the very same files work whether the flag
  is on or off, and you can switch back and forth freely.

## Relative phrases still work

Natural-language dates are calendar-agnostic — the same number of days is the
same span in either calendar. So these behave identically with the flag on:

```sh
jasem todo "submit report tomorrow, work"
jasem todo "renew passport in 3 weeks"
jasem track "2h design work yesterday"
```

`tomorrow`, `next friday`, `in 3 days`, weekday names, etc. all resolve the same
way; only the **displayed** date and any **explicit numeric date you type** are
Jalali. See [[Natural Language Input]] for the full phrase list.

## Turning it off

Leave `JASEM_JALALI` unset (or set it to `false`/`0`/`no`/`off`) for the default
Gregorian calendar. Because storage is always Gregorian, nothing in your files
needs to change.

## See also

* [[Configuration]] — all environment variables
* [[Data Files]] — why on-disk dates stay Gregorian
