"""Construction of the colorized ``jasem help`` text."""

from ..shared.calendar_view import CalendarView


def render_help(console, config):
    """Return the full help screen as a single string.

    Args:
        console: Console used to style the text.
        config: Config whose provider, model, and file paths are shown.

    Returns:
        The complete, ready-to-print help text.
    """
    header = lambda text: "\n" + console.bold(console.cyan(text))
    command = console.green
    example = console.yellow
    note = console.dim
    calendar = CalendarView.from_config(config)
    date_example = calendar.format_iso("2026-07-01")

    def row(left, right):
        """Return an aligned ``key -> value`` help row."""
        return "  " + console.green(left.ljust(24)) + right

    sections = [
        console.bold("jasem") + note(" — plain-text task manager + time tracker + spending log, pluggable AI parsing"),

        header("ADD") + note("  wrap the task in quotes; deadline, priority & tags auto-detected"),
        "  " + command('jasem "') + example("pay rent next friday, high priority, finance") + command('"'),
        "  " + command('jasem "') + example("review Ali PR by tomorrow, work") + command('"'),
        "  " + command('jasem add "') + example("…") + command('"') + note("   force-add even if text starts with a command word"),
        "  " + note("quotes keep shell chars (& ! * ( )) and words like done/list literal"),

        header("VIEW") + note("  append a category to filter, e.g. ") + command("jasem list work"),
        row("jasem list  (ls)", "open tasks, soonest deadline first"),
        row("jasem today", "due today"),
        row("jasem week", "due within the next 7 days"),
        row("jasem overdue", "past deadline, not done  " + console.red("(red)")),
        row("jasem all", "everything, including completed"),
        row("jasem tags", "list categories in use, with counts"),

        header("UPDATE"),
        row("jasem done <id>…", "mark task(s) complete"),
        row("jasem rm <id>…", "delete task(s) permanently"),
        row("jasem set <id> priority", example("high · medium · low")),
        row("jasem set <id> deadline", example(f"next friday · in 3 days · {date_example} · none")),
        row("jasem set <id> category", example("work finance")
            + note("  (space/comma-separated; ") + example("none") + note(" clears)")),

        header("TIME TRACKING") + note("  describe the work naturally; duration, date & tag auto-detected"),
        "  " + command('jasem track "') + example("1h45min debugging the parser yesterday, work") + command('"'),
        "  " + command('jasem track "') + example("spent half an hour on emails") + command('"'),
        "  " + note("commas optional; date blank = today, tag blank = work; logging prints the entry id"),
        row("jasem track rm <id>…", "delete tracked entries"),
        row("jasem track set <id>", example("time 1h30min · work \"…\" · date yesterday · tag personal")),
        "  " + note("review tracked time with ") + command("jasem report") + note("  (see REPORTS below)"),

        header("REPORTS") + note("  stats + bar charts over tracked time; append a tag to filter"),
        row("jasem report", "this week: totals, by-tag, daily timeline & top activities"),
        row("jasem report week", "same as bare report (last 7 days)"),
        row("jasem report month", "last 30 days"),
        row("jasem report all", "everything, e.g. " + command("jasem report all work")),

        header("SPENDING") + note("  record money spent naturally; amount, date & tag auto-detected"),
        "  " + command('jasem acc "') + example("50k lunch with the team yesterday, food") + command('"'),
        "  " + command('jasem acc "') + example("1.5m new phone") + command('"'),
        "  " + note("commas optional; date blank = today, tag blank = general; recording prints the id"),
        row("jasem acc list [tag]", "recorded spending, oldest first, optionally by category"),
        row("jasem acc rm <id>…", "delete spending record(s)"),
        row("jasem acc set <id>", example('amount 60k · title "…" · description "…" · date yesterday · tag food')),
        row("jasem acc report", "totals, by-tag, timeline & top spends (period + tag like report)"),
        row("jasem acc tags", "list spending categories in use, with counts"),

        header("AI PARSING") + note("  add & track call a model; pick a backend with JASEM_PROVIDER"),
        row("  ollama  (default)", note("local, no key — run ") + command("ollama serve") + note(" + a small model")),
        row("  openai", note("any OpenAI-compatible API — set ") + example("JASEM_API_KEY")
            + note(" (+ ") + example("JASEM_OPENAI_API_BASE") + note(" or ") + example("OPENAI_BASE_URL")
            + note(" for non-OpenAI hosts)")),
        row("  anthropic", note("Claude — set ") + example("JASEM_PROVIDER=anthropic") + note(" + ") + example("JASEM_API_KEY")),
        "  " + note("if the backend is unreachable, entries are still saved (regex dates; track falls back to the comma format)."),

        header("FILES & CONFIG"),
        row("  provider", example(config.provider) + note("   (JASEM_PROVIDER: ollama · openai · anthropic)")),
        row("  model", example(config.model) + note("   (JASEM_MODEL)")),
        row("  tasks", config.task_file + note("  (plain Markdown, hand-editable)")),
        row("  time log", config.track_file + note("  (plain Markdown)")),
        row("  spending", config.spend_file + note("  (plain Markdown)")),
        row("  calendar", example("Jalali" if config.jalali else "Gregorian")
            + note("   (JASEM_JALALI; data on disk stays Gregorian)")),
        row("  env vars", note("JASEM_DIR · JASEM_FILE · JASEM_TRACK_FILE · JASEM_SPEND_FILE · "
                               "JASEM_PROVIDER · JASEM_MODEL · JASEM_API_KEY · "
                               "JASEM_OPENAI_API_BASE · JASEM_API_BASE · OLLAMA_HOST · JASEM_JALALI")),
    ]
    return "\n".join(sections)
