#!/usr/bin/env python3
"""jasem — a plain-text task manager and time tracker.

Add tasks in natural language; an AI backend extracts the structure and plain
Python resolves the deadline to a real date. Storage is a human-readable
Markdown table. By default everything runs locally (Ollama); you can point it
at any OpenAI-compatible API or at Anthropic instead. If no AI is reachable,
tasks are still saved (with regex-based date parsing).

Usage:
  jasem <free text>        Add a task, e.g.  jasem pay rent next friday, high, finance
  jasem add <free text>    Same as above (explicit)
  jasem list | ls          Show open tasks, soonest deadline first
  jasem today              Tasks due today
  jasem overdue            Tasks past their deadline (not done)
  jasem week               Tasks due within the next 7 days
  jasem done <id> [id...]  Mark task(s) complete
  jasem set <id> <field> <value>   Change priority, deadline, or category
  jasem rm <id> [id...]    Delete task(s)
  jasem all                Show everything, including completed
  jasem tags               List categories in use, with counts
  jasem track "<time>, <work>[, <date>][, <tag>]"
                           Log time spent; date blank = today, tag blank = work
  jasem track [today|week|all] [tag]
                           Show the time log grouped by day, with totals
  jasem help               This help

AI parsing (the only step that uses a model):
  JASEM_PROVIDER   ollama (default) | openai | anthropic
  JASEM_MODEL      model id (default per provider)
  JASEM_API_KEY    API key for openai/anthropic (falls back to
                   OPENAI_API_KEY / ANTHROPIC_API_KEY)
  JASEM_API_BASE   base URL override (any OpenAI-compatible endpoint;
                   default https://api.openai.com/v1 or https://api.anthropic.com)
  OLLAMA_HOST      default http://localhost:11434

Storage (plain Markdown, hand-editable):
  JASEM_DIR        default ~/.jasem
  JASEM_FILE       default $JASEM_DIR/tasks.md
  JASEM_TRACK_FILE default $JASEM_DIR/timelog.md
"""

import os
import sys
import re
import json
import calendar
import datetime as dt
import urllib.request
import urllib.error

# ---------- AI backend configuration ----------
PROVIDER = os.environ.get("JASEM_PROVIDER", "ollama").strip().lower()
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
API_BASE = os.environ.get("JASEM_API_BASE", "").rstrip("/")
API_KEY = (
    os.environ.get("JASEM_API_KEY")
    or os.environ.get("OPENAI_API_KEY")
    or os.environ.get("ANTHROPIC_API_KEY")
    or ""
)
_DEFAULT_MODEL = {
    "ollama": "qwen2.5:3b",
    "openai": "gpt-4o-mini",
    "anthropic": "claude-opus-4-8",
}
MODEL = os.environ.get("JASEM_MODEL") or _DEFAULT_MODEL.get(PROVIDER, "qwen2.5:3b")

# ---------- storage configuration ----------
JASEM_DIR = os.path.expanduser(os.environ.get("JASEM_DIR", "~/.jasem"))
TASK_FILE = os.path.expanduser(
    os.environ.get("JASEM_FILE", os.path.join(JASEM_DIR, "tasks.md"))
)
TRACK_FILE = os.path.expanduser(
    os.environ.get("JASEM_TRACK_FILE", os.path.join(JASEM_DIR, "timelog.md"))
)

COLS = ["ID", "✓", "Priority", "Deadline", "Task", "Tags", "Created"]
TRACK_COLS = ["Date", "Time", "Work", "Tag"]
PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}

# ---------- ANSI colors (only when writing to a real terminal) ----------
_TTY = sys.stdout.isatty()
def _c(code, s):
    return f"\033[{code}m{s}\033[0m" if _TTY else s
RED    = lambda s: _c("31", s)
YELLOW = lambda s: _c("33", s)
GREEN  = lambda s: _c("32", s)
DIM    = lambda s: _c("2", s)
BOLD   = lambda s: _c("1", s)
CYAN   = lambda s: _c("36", s)


# ===================== date resolution (pure Python) =====================
WEEKDAYS = {n.lower(): i for i, n in enumerate(calendar.day_name)}
WEEKDAYS.update({n.lower(): i for i, n in enumerate(calendar.day_abbr)})
MONTHS = {n.lower(): i for i, n in enumerate(calendar.month_name) if n}
MONTHS.update({n.lower(): i for i, n in enumerate(calendar.month_abbr) if n})

NO_DATE = {"", "none", "no deadline", "no date", "n/a", "na", "null", "someday", "-"}

# Words that mean "empty this field" when editing a task.
CLEAR_WORDS = {"none", "no", "clear", "remove", "-", "n/a", "na", "null", ""}


def _add_months(d, n):
    m = d.month - 1 + n
    y = d.year + m // 12
    m = m % 12 + 1
    return dt.date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def _next_weekday(today, target, include_today=False):
    days = (target - today.weekday()) % 7
    if days == 0 and not include_today:
        days = 7
    return today + dt.timedelta(days=days)


def resolve_date(phrase, today, llm_date=""):
    """Turn a temporal phrase into YYYY-MM-DD, or '' for no deadline."""
    def fallback():
        d = (llm_date or "").strip()
        return d if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d) else ""

    p = (phrase or "").strip().lower()
    if p in NO_DATE:
        return fallback()

    # explicit ISO date anywhere in the phrase
    m = re.search(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b", p)
    if m:
        try:
            return dt.date(int(m[1]), int(m[2]), int(m[3])).isoformat()
        except ValueError:
            pass

    # "in N day(s)/week(s)/month(s)"
    m = re.search(r"\bin\s+(\d+)\s+(day|week|month)s?\b", p)
    if m:
        n, unit = int(m[1]), m[2]
        if unit == "day":
            return (today + dt.timedelta(days=n)).isoformat()
        if unit == "week":
            return (today + dt.timedelta(days=7 * n)).isoformat()
        return _add_months(today, n).isoformat()

    # "next <weekday>" -> always strictly in the future
    m = re.search(r"\bnext\s+(\w+)", p)
    if m and m[1] in WEEKDAYS:
        return _next_weekday(today, WEEKDAYS[m[1]], include_today=False).isoformat()

    # relative day words (match whether input is a clean phrase or a full sentence)
    if re.search(r"\btomorrow\b", p):
        return (today + dt.timedelta(days=1)).isoformat()
    if re.search(r"\byesterday\b", p):
        return (today - dt.timedelta(days=1)).isoformat()
    if re.search(r"\b(today|tonight|now)\b", p):
        return today.isoformat()
    if re.search(r"\bnext\s+week\b", p):
        return (today + dt.timedelta(days=7)).isoformat()
    if re.search(r"\bnext\s+month\b", p):
        return _add_months(today, 1).isoformat()
    if re.search(r"\b(eow|end of week|this week)\b", p):
        return _next_weekday(today, 4, include_today=True).isoformat()  # Friday

    # "this <weekday>" or a bare weekday -> next occurrence (today counts)
    for name, idx in WEEKDAYS.items():
        if re.search(rf"\b{re.escape(name)}\b", p):
            return _next_weekday(today, idx, include_today=True).isoformat()

    # "<month> <day>[ , year]"
    m = re.search(r"([a-z]+)\s+(\d{1,2})(?:,?\s*(\d{4}))?", p)
    if m and m[1] in MONTHS:
        year = int(m[3]) if m[3] else today.year
        try:
            d = dt.date(year, MONTHS[m[1]], int(m[2]))
            if not m[3] and d < today:
                d = dt.date(year + 1, MONTHS[m[1]], int(m[2]))
            return d.isoformat()
        except ValueError:
            pass

    # "<day> <month>[ , year]"
    m = re.search(r"(\d{1,2})\s+([a-z]+)(?:,?\s*(\d{4}))?", p)
    if m and m[2] in MONTHS:
        year = int(m[3]) if m[3] else today.year
        try:
            d = dt.date(year, MONTHS[m[2]], int(m[1]))
            if not m[3] and d < today:
                d = dt.date(year + 1, MONTHS[m[2]], int(m[1]))
            return d.isoformat()
        except ValueError:
            pass

    return fallback()


# ===================== AI parsing (pluggable backend) =====================
SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "deadline_phrase": {"type": "string"},
        "deadline_date": {"type": "string"},
        "priority": {"type": "string", "enum": ["low", "medium", "high"]},
        "tags": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["title", "deadline_phrase", "deadline_date", "priority", "tags"],
}

_JSON_SYS = (
    "You output only a single JSON object with the requested fields. "
    "No prose, no markdown, no code fences."
)


def _build_prompt(text, today):
    rules = (
        "Extract structured fields from the task description below.\n"
        "- title: short imperative summary, WITHOUT any date/priority/tag words.\n"
        "- deadline_phrase: the exact temporal words as written, for example "
        "next thursday / tomorrow / june 20 / in 3 days; empty string if none.\n"
        "- deadline_date: your best YYYY-MM-DD guess for the deadline, empty string if none.\n"
        "- priority: low, medium, or high (default medium).\n"
        "- tags: short topic words mentioned such as work, finance, personal; "
        "empty list if none.\n"
        "Always capture any time words (tomorrow, friday, next week, by june 20) "
        "in deadline_phrase, even when they follow words like 'by' or 'due'.\n"
    )
    examples = (
        'Example. Task: "review Ali PR by tomorrow, work" -> '
        '{"title": "review Ali PR", "deadline_phrase": "tomorrow", '
        '"deadline_date": "", "priority": "medium", "tags": ["work"]}\n'
        'Example. Task: "pay rent next friday high priority" -> '
        '{"title": "pay rent", "deadline_phrase": "next friday", '
        '"deadline_date": "", "priority": "high", "tags": []}\n'
    )
    return (
        f"Today is {today.isoformat()} ({today.strftime('%A')}).\n"
        f"{rules}\n{examples}\nTask: {text}"
    )


def _http_json(url, payload, headers, timeout=120):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", **headers},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def _extract_json(text):
    """Pull a JSON object out of a model reply (tolerates code fences / prose)."""
    text = (text or "").strip()
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        text = m.group(1)
    try:
        return json.loads(text)
    except ValueError:
        start = text.find("{")
        if start < 0:
            raise
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(text[start:i + 1])
        raise


def _parse_ollama(prompt):
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "format": SCHEMA,            # Ollama constrains output to this schema
        "options": {"temperature": 0},
    }
    resp = _http_json(OLLAMA_HOST + "/api/chat", payload, {})
    return json.loads(resp["message"]["content"])


def _parse_openai(prompt):
    base = API_BASE or "https://api.openai.com/v1"
    headers = {"Authorization": "Bearer " + API_KEY} if API_KEY else {}
    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": _JSON_SYS},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    try:
        resp = _http_json(base + "/chat/completions", body, headers)
    except urllib.error.HTTPError as e:
        if e.code == 400:  # some compatible servers reject response_format
            body.pop("response_format", None)
            resp = _http_json(base + "/chat/completions", body, headers)
        else:
            raise
    return _extract_json(resp["choices"][0]["message"]["content"])


def _parse_anthropic(prompt):
    base = API_BASE or "https://api.anthropic.com"
    headers = {"x-api-key": API_KEY, "anthropic-version": "2023-06-01"}
    body = {
        "model": MODEL,
        "max_tokens": 1024,
        # Force a tool call so the structured fields come back validated.
        "tools": [{
            "name": "record_task",
            "description": "Record the structured fields extracted from the task.",
            "input_schema": SCHEMA,
        }],
        "tool_choice": {"type": "tool", "name": "record_task"},
        "messages": [{"role": "user", "content": prompt}],
    }
    resp = _http_json(base + "/v1/messages", body, headers)
    for block in resp.get("content", []):
        if block.get("type") == "tool_use":
            return block.get("input", {})
    raise ValueError("Anthropic response contained no tool_use block")


PROVIDERS = {
    "ollama": _parse_ollama,
    "openai": _parse_openai,
    "anthropic": _parse_anthropic,
}


def llm_parse(text, today):
    fn = PROVIDERS.get(PROVIDER)
    if fn is None:
        raise ValueError(
            f"unknown JASEM_PROVIDER={PROVIDER!r}; use ollama, openai, or anthropic"
        )
    return fn(_build_prompt(text, today))


def parse_task(text):
    today = dt.date.today()
    try:
        d = llm_parse(text, today)
        title = (d.get("title") or text).strip()
        deadline = resolve_date(
            d.get("deadline_phrase", ""), today, d.get("deadline_date", "")
        )
        # Models sometimes miss the deadline phrase; deterministically rescan
        # the original text as a fallback before giving up.
        if not deadline:
            deadline = resolve_date(text, today)
        priority = d.get("priority", "medium")
        if priority not in PRIORITY_RANK:
            priority = "medium"
        tags = [str(t).strip() for t in d.get("tags", []) if str(t).strip()]
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        sys.stderr.write(
            RED(f"! Could not reach the {PROVIDER} backend ({e}); storing raw text.\n")
            + DIM("  Check JASEM_PROVIDER / JASEM_MODEL / JASEM_API_KEY, "
                  "or that 'ollama serve' is running.\n")
        )
        title, deadline, priority, tags = _local_parse(text, today)
    except Exception as e:
        sys.stderr.write(RED(f"! Parse error ({e}); storing raw text.\n"))
        title, deadline, priority, tags = _local_parse(text, today)
    return {
        "done": False,
        "priority": priority,
        "deadline": deadline,
        "title": _clean(title),
        "tags": ", ".join(tags),
        "created": today.isoformat(),
    }


def _local_parse(text, today):
    """No-AI fallback: keep the raw text, still resolve any date words in it."""
    return text.strip(), resolve_date(text, today), "medium", []


def _clean(s):
    # Pipes would break the Markdown table; newlines too.
    return s.replace("|", "/").replace("\n", " ").strip()


# ===================== Markdown storage =====================
PREAMBLE = (
    "# Tasks\n\n"
    "_Managed by the `jasem` CLI. You can hand-edit rows, but keep the column order._\n\n"
)


def load():
    if not os.path.exists(TASK_FILE):
        return []
    tasks = []
    with open(TASK_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 7:
                continue
            if cells[0] == "ID" or set(cells[0]) <= set("-: "):
                continue  # header or separator row
            try:
                tid = int(cells[0])
            except ValueError:
                continue
            tasks.append({
                "id": tid,
                "done": cells[1] == "☑",
                "priority": cells[2] or "medium",
                "deadline": cells[3] if cells[3] != "-" else "",
                "title": cells[4],
                "tags": cells[5] if cells[5] != "-" else "",
                "created": cells[6],
            })
    return tasks


def save(tasks):
    rows = [COLS, ["-" * len(c) for c in COLS]]
    for t in tasks:
        rows.append([
            str(t["id"]),
            "☑" if t["done"] else "☐",
            t["priority"],
            t["deadline"] or "-",
            t["title"],
            t["tags"] or "-",
            t["created"],
        ])
    widths = [max(len(r[i]) for r in rows) for i in range(len(COLS))]
    lines = []
    for ri, r in enumerate(rows):
        if ri == 1:  # separator row uses dashes padded with dashes
            lines.append("| " + " | ".join("-" * widths[i] for i in range(len(COLS))) + " |")
        else:
            lines.append("| " + " | ".join(r[i].ljust(widths[i]) for i in range(len(COLS))) + " |")
    os.makedirs(os.path.dirname(TASK_FILE), exist_ok=True)
    with open(TASK_FILE, "w", encoding="utf-8") as f:
        f.write(PREAMBLE + "\n".join(lines) + "\n")


def next_id(tasks):
    return max((t["id"] for t in tasks), default=0) + 1


# ===================== display =====================
def _sort_key(t):
    # open first, then by deadline (none last), then priority
    return (
        t["done"],
        t["deadline"] or "9999-99-99",
        PRIORITY_RANK.get(t["priority"], 1),
    )


def show(tasks, header):
    today = dt.date.today().isoformat()
    if not tasks:
        print(DIM("  (nothing here)"))
        return
    print(BOLD(header))
    for t in sorted(tasks, key=_sort_key):
        mark = GREEN("☑") if t["done"] else "☐"
        dl = t["deadline"] or "—"
        if not t["done"] and t["deadline"]:
            if t["deadline"] < today:
                dl = RED(dl + " (overdue)")
            elif t["deadline"] == today:
                dl = YELLOW(dl + " (today)")
        prio = t["priority"]
        if prio == "high":
            prio = BOLD(RED(prio))
        elif prio == "low":
            prio = DIM(prio)
        tags = DIM(f"#{t['tags'].replace(', ', ' #')}") if t["tags"] else ""
        title = DIM(t["title"]) if t["done"] else t["title"]
        print(f"  {mark} {CYAN(str(t['id']).rjust(3))}  [{prio}]  {dl}  {title}  {tags}")


# ===================== commands =====================
def cmd_add(text):
    tasks = load()
    t = parse_task(text)
    t["id"] = next_id(tasks)
    tasks.append(t)
    save(tasks)
    dl = t["deadline"] or "no deadline"
    print(GREEN("✓ added"), f"#{t['id']}:", BOLD(t["title"]))
    print(DIM(f"  priority={t['priority']}  deadline={dl}"
              + (f"  tags={t['tags']}" if t["tags"] else "")))


def cmd_done(ids):
    tasks = load()
    hit = [t for t in tasks if t["id"] in ids]
    for t in hit:
        t["done"] = True
    save(tasks)
    if hit:
        print(GREEN("✓ completed:"), ", ".join(f"#{t['id']} {t['title']}" for t in hit))
    else:
        print(RED("no matching id(s)"))


def cmd_rm(ids):
    tasks = load()
    keep = [t for t in tasks if t["id"] not in ids]
    removed = len(tasks) - len(keep)
    save(keep)
    print(GREEN(f"✓ removed {removed} task(s)") if removed else RED("no matching id(s)"))


# Field name -> accepted aliases, for `jasem set <id> <field> <value>`.
SET_FIELDS = {
    "priority": {"priority", "prio", "p"},
    "deadline": {"deadline", "due", "date", "d"},
    "category": {"category", "categories", "tag", "tags", "c"},
}


def _resolve_field(name):
    name = name.lower()
    for field, aliases in SET_FIELDS.items():
        if name in aliases:
            return field
    return None


def cmd_set(args):
    if len(args) < 3:
        print(RED("usage: jasem set <id> <priority|deadline|category> <value>"))
        print(DIM("  e.g.  jasem set 3 priority high"))
        print(DIM("        jasem set 3 deadline next friday"))
        print(DIM("        jasem set 3 category work finance     (none clears it)"))
        return

    try:
        tid = int(args[0])
    except ValueError:
        print(RED(f"not a valid id: {args[0]}"))
        return

    field = _resolve_field(args[1])
    if not field:
        print(RED(f"unknown field: {args[1]}"))
        print(DIM("  fields: priority · deadline · category"))
        return
    value = " ".join(args[2:]).strip()

    tasks = load()
    t = next((x for x in tasks if x["id"] == tid), None)
    if not t:
        print(RED(f"no task with id #{tid}"))
        return

    if field == "priority":
        v = value.lower()
        if v not in PRIORITY_RANK:
            print(RED(f"priority must be one of: {', '.join(PRIORITY_RANK)}"))
            return
        t["priority"] = v
        msg = f"priority → {v}"
    elif field == "deadline":
        if value.lower() in CLEAR_WORDS:
            t["deadline"] = ""
            msg = "deadline cleared"
        else:
            resolved = resolve_date(value, dt.date.today())
            if not resolved:
                print(RED(f"could not understand deadline: {value!r}"))
                print(DIM("  try: tomorrow · next friday · in 3 days · "
                          "june 20 · 2026-07-01 · none"))
                return
            t["deadline"] = resolved
            msg = f"deadline → {resolved}"
    else:  # category
        if value.lower() in CLEAR_WORDS:
            t["tags"] = ""
            msg = "category cleared"
        else:
            parts = [p for p in (s.strip() for s in re.split(r"[,\s]+", value)) if p]
            t["tags"] = _clean(", ".join(parts))
            msg = f"category → {t['tags']}"

    save(tasks)
    print(GREEN(f"✓ #{tid} updated:"), msg)
    print(DIM(f"  {t['title']}"))


def _tags_of(t):
    """Lower-cased list of categories/tags on a task."""
    return [x.strip().lower() for x in t["tags"].split(",") if x.strip()]


def cmd_tags():
    counts = {}
    for t in load():
        if t["done"]:
            continue
        for tag in _tags_of(t):
            counts[tag] = counts.get(tag, 0) + 1
    if not counts:
        print(DIM("  (no categories yet)"))
        return
    print(BOLD("Categories — open tasks"))
    for tag, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  {n:>3}  {CYAN('#' + tag)}")


# ===================== time tracking =====================
TRACK_PREAMBLE = (
    "# Time log\n\n"
    "_Managed by the `jasem track` CLI. Hand-edit rows freely, but keep the column order._\n\n"
)

# Longest unit spellings first so e.g. "min" wins over a bare "m".
_DUR_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(hours|hour|hrs|hr|h|minutes|minute|mins|min|m)\b"
)


def parse_duration(text):
    """Best-effort minutes from free text like '2h', '30 min', '1h 30min'. 0 if unreadable."""
    s = (text or "").lower()
    total = 0.0
    for m in _DUR_RE.finditer(s):
        total += float(m[1]) * 60 if m[2][0] == "h" else float(m[1])
    if total == 0:  # a bare number means minutes
        m = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*", s)
        if m:
            total = float(m[1])
    return int(round(total))


def fmt_duration(mins):
    h, m = divmod(int(mins), 60)
    if h and m:
        return f"{h}h {m}min"
    return f"{h}h" if h else f"{m}min"


def track_load():
    if not os.path.exists(TRACK_FILE):
        return []
    out = []
    with open(TRACK_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 4:
                continue
            if cells[0] == "Date" or set(cells[0]) <= set("-: "):
                continue  # header or separator row
            out.append({"date": cells[0], "time": cells[1],
                        "work": cells[2], "tag": cells[3]})
    return out


def track_save(entries):
    rows = [TRACK_COLS, ["-" * len(c) for c in TRACK_COLS]]
    for e in entries:
        rows.append([e["date"], e["time"], e["work"], e["tag"] or "work"])
    widths = [max(len(r[i]) for r in rows) for i in range(len(TRACK_COLS))]
    lines = []
    for ri, r in enumerate(rows):
        if ri == 1:
            lines.append("| " + " | ".join("-" * widths[i] for i in range(len(TRACK_COLS))) + " |")
        else:
            lines.append("| " + " | ".join(r[i].ljust(widths[i]) for i in range(len(TRACK_COLS))) + " |")
    os.makedirs(os.path.dirname(TRACK_FILE), exist_ok=True)
    with open(TRACK_FILE, "w", encoding="utf-8") as f:
        f.write(TRACK_PREAMBLE + "\n".join(lines) + "\n")


def track_add(text):
    """Parse '<time>, <work>[, <date>][, <tag>]' and append a log entry."""
    parts = [p.strip() for p in text.split(",") if p.strip()]
    if len(parts) < 2:
        print(RED('usage: jasem track "<time>, <work>[, <date>][, <tag>]"'))
        print(DIM('  e.g.  jasem track "2h, coding"'))
        print(DIM('        jasem track "30 min, coding, yesterday, work"'))
        return
    today = dt.date.today()
    time_text, work, extra = parts[0], parts[1], parts[2:]
    # Of the trailing fields, the one that reads as a date is the date; the
    # other is the tag — so order between them doesn't matter.
    date_s, tag = "", ""
    for item in extra:
        resolved = resolve_date(item, today)
        if resolved and not date_s:
            date_s = resolved
        elif not tag:
            tag = item
    date_s = date_s or today.isoformat()
    tag = tag or "work"

    entries = track_load()
    entries.append({"date": date_s, "time": _clean(time_text),
                    "work": _clean(work), "tag": _clean(tag)})
    track_save(entries)

    mins = parse_duration(time_text)
    when = "today" if date_s == today.isoformat() else date_s
    print(GREEN("✓ tracked"), BOLD(time_text), DIM("·"), work,
          DIM(f"· {when} · #{tag}"))
    if mins == 0:
        sys.stderr.write(YELLOW(
            f"  (couldn't read a duration from {time_text!r}; "
            "stored as-is, won't count toward totals)\n"))


def track_view(period, tag_filter):
    entries = track_load()
    today = dt.date.today()
    today_s = today.isoformat()
    if period == "all":
        sel, header = entries, "Time log — all"
    elif period == "week":
        since = (today - dt.timedelta(days=6)).isoformat()
        sel = [e for e in entries if e["date"] >= since]
        header = "Time log — last 7 days"
    else:  # today
        sel = [e for e in entries if e["date"] == today_s]
        header = "Time log — today"
    if tag_filter:
        sel = [e for e in sel if e["tag"].lower() == tag_filter]
        header += "  ·  #" + tag_filter

    if not sel:
        print(BOLD(header))
        print(DIM("  (nothing tracked)"))
        return

    by_date = {}
    for e in sel:
        by_date.setdefault(e["date"], []).append(e)
    grand = 0
    print(BOLD(header))
    for date in sorted(by_date, reverse=True):
        day = by_date[date]
        total = sum(parse_duration(e["time"]) for e in day)
        grand += total
        label = date + (" (today)" if date == today_s else "")
        print("\n  " + BOLD(CYAN(label)) + DIM("  —  ") + BOLD(fmt_duration(total)))
        for e in day:
            tg = DIM(f"#{e['tag']}") if e["tag"] else ""
            print(f"    {e['time'].rjust(9)}   {e['work']}  {tg}")
    if len(by_date) > 1:
        print("\n  " + DIM("total ") + BOLD(fmt_duration(grand)))


def cmd_track(args):
    text = " ".join(args).strip()
    words = text.split()
    first = words[0].lower() if words else ""
    # A new entry has comma-separated fields. A bare duration with no comma is
    # a half-typed entry (missing the work) -> route to add for the usage hint,
    # not to the viewer where it would be mistaken for a tag filter.
    if "," in text or (first not in ("today", "week", "all") and parse_duration(text)):
        track_add(text)
        return
    period = "today"
    if words and words[0] in ("today", "week", "all"):
        period = words.pop(0)
    tag_filter = words[0].lower() if words else None
    track_view(period, tag_filter)


def usage():
    H = lambda s: "\n" + BOLD(CYAN(s))              # section header
    cmd = lambda s: GREEN(s)                          # command
    ex = lambda s: YELLOW(s)                          # example / value
    d = DIM                                           # de-emphasised note

    def row(left, right):                             # aligned key -> value row
        return "  " + GREEN(left.ljust(24)) + right

    out = [
        BOLD("jasem") + d(" — plain-text task manager + time tracker, pluggable AI parsing"),

        H("ADD") + d("  wrap the task in quotes; deadline, priority & tags auto-detected"),
        "  " + cmd('jasem "') + ex("pay rent next friday, high priority, finance") + cmd('"'),
        "  " + cmd('jasem "') + ex("review Ali PR by tomorrow, work") + cmd('"'),
        "  " + cmd('jasem add "') + ex("…") + cmd('"') + d("   force-add even if text starts with a command word"),
        "  " + d("quotes keep shell chars (& ! * ( )) and words like done/list literal"),

        H("VIEW") + d("  append a category to filter, e.g. ") + cmd("jasem list work"),
        row("jasem list  (ls)", "open tasks, soonest deadline first"),
        row("jasem today", "due today"),
        row("jasem week", "due within the next 7 days"),
        row("jasem overdue", "past deadline, not done  " + RED("(red)")),
        row("jasem all", "everything, including completed"),
        row("jasem tags", "list categories in use, with counts"),

        H("UPDATE"),
        row("jasem done <id>…", "mark task(s) complete"),
        row("jasem rm <id>…", "delete task(s) permanently"),
        row("jasem set <id> priority", ex("high · medium · low")),
        row("jasem set <id> deadline", ex("next friday · in 3 days · 2026-07-01 · none")),
        row("jasem set <id> category", ex("work finance")
            + d("  (space/comma-separated; ") + ex("none") + d(" clears)")),

        H("TIME TRACKING") + d("  log durations as plain text; date blank = today, tag blank = work"),
        "  " + cmd('jasem track "') + ex("2h, coding") + cmd('"'),
        "  " + cmd('jasem track "') + ex("30 min, coding, yesterday, work") + cmd('"'),
        "  " + d("format: ") + ex('"<time>, <work>[, <date>][, <tag>]"'),
        row("jasem track", "today's entries, with a daily total"),
        row("jasem track week", "last 7 days, grouped by day"),
        row("jasem track all", "everything; append a tag to filter, e.g. " + cmd("jasem track week work")),

        H("AI PARSING") + d("  the only step that calls a model; pick a backend with JASEM_PROVIDER"),
        row("  ollama  (default)", d("local, no key — run ") + cmd("ollama serve") + d(" + a small model")),
        row("  openai", d("any OpenAI-compatible API — set ") + ex("JASEM_API_KEY")
            + d(" (+ ") + ex("JASEM_API_BASE") + d(" for non-OpenAI hosts)")),
        row("  anthropic", d("Claude — set ") + ex("JASEM_PROVIDER=anthropic") + d(" + ") + ex("JASEM_API_KEY")),
        "  " + d("if the backend is unreachable, the task is still saved (regex dates, no tags)."),

        H("FILES & CONFIG"),
        row("  provider", ex(PROVIDER) + d("   (JASEM_PROVIDER: ollama · openai · anthropic)")),
        row("  model", ex(MODEL) + d("   (JASEM_MODEL)")),
        row("  tasks", TASK_FILE + d("  (plain Markdown, hand-editable)")),
        row("  time log", TRACK_FILE + d("  (plain Markdown)")),
        row("  env vars", d("JASEM_DIR · JASEM_FILE · JASEM_TRACK_FILE · JASEM_PROVIDER · "
                            "JASEM_MODEL · JASEM_API_KEY · JASEM_API_BASE · OLLAMA_HOST")),
    ]
    print("\n".join(out))


def main(argv):
    if not argv or argv[0] in ("help", "-h", "--help"):
        usage()
        return
    cmd = argv[0]
    rest = argv[1:]
    today = dt.date.today()
    today_s = today.isoformat()
    wk_s = (today + dt.timedelta(days=7)).isoformat()

    VIEWS = {
        "list": (lambda t: not t["done"], "Open tasks"),
        "ls": (lambda t: not t["done"], "Open tasks"),
        "all": (lambda t: True, "All tasks"),
        "today": (lambda t: not t["done"] and t["deadline"] == today_s, "Due today"),
        "week": (lambda t: not t["done"] and t["deadline"]
                 and today_s <= t["deadline"] <= wk_s, "Due within 7 days"),
        "overdue": (lambda t: not t["done"] and t["deadline"]
                    and t["deadline"] < today_s, "Overdue"),
    }

    if cmd == "tags":
        cmd_tags()
    elif cmd in VIEWS:
        pred, header = VIEWS[cmd]
        tasks = [t for t in load() if pred(t)]
        if rest:  # optional category filter(s): jasem list work [urgent]
            cats = [c.strip().lower() for c in rest]
            tasks = [t for t in tasks if all(c in _tags_of(t) for c in cats)]
            header += "  ·  " + " ".join("#" + c for c in cats)
        show(tasks, header)
    elif cmd in ("done", "rm"):
        ids = set()
        for a in rest:
            try:
                ids.add(int(a))
            except ValueError:
                pass
        if not ids:
            print(RED(f"usage: jasem {cmd} <id> [id...]"))
            print(DIM(f'  (to add a task that starts with "{cmd}", quote it: '
                      f'jasem add "{cmd} ...")'))
            return
        (cmd_done if cmd == "done" else cmd_rm)(ids)
    elif cmd in ("set", "edit"):
        cmd_set(rest)
    elif cmd == "track":
        cmd_track(rest)
    elif cmd == "add":
        if len(argv) < 2:
            print(RED("usage: jasem add <description>"))
            return
        cmd_add(" ".join(argv[1:]))
    else:
        # no recognized subcommand -> treat the whole input as a new task
        cmd_add(" ".join(argv))


def cli():
    """Console-script entry point (see pyproject.toml [project.scripts])."""
    main(sys.argv[1:])


if __name__ == "__main__":
    cli()
