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
    header = lambda text: "\n" + console.bold(console.accent(text))
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
        note("three namespaces — ") + command("todo") + note(" · ") + command("track") + note(" · ")
        + command("acc") + note(" — each sharing the same verbs: ")
        + note("<text>=add · list · tags · rm · set"),

        header("TASKS") + note("  ") + command("jasem todo …") + note("   deadline, priority & tags auto-detected"),
        "  " + command('jasem todo "') + example("pay rent next friday, high priority, finance") + command('"'),
        "  " + command('jasem todo "') + example("review Ali PR by tomorrow, work") + command('"'),
        row("jasem todo  (no args)", "open tasks, soonest deadline first"),
        row("jasem todo list (ls)", "same; append a category, e.g. " + command("jasem todo list work")),
        row("jasem todo today", "due today"),
        row("jasem todo week", "due within the next 7 days"),
        row("jasem todo overdue", "past deadline, not done  " + console.red("(red)")),
        row("jasem todo all", "everything, including completed"),
        row("jasem todo tags", "list categories in use, with counts"),
        row('jasem todo find "…"', "search task titles & tags"),
        row("jasem todo done <id>…", "mark task(s) complete"),
        row("jasem todo rm <id>…", "delete task(s) permanently"),
        row("jasem todo set <id>", example("priority high · deadline next friday · category work finance")),
        "  " + note("    priority ") + example("high·medium·low") + note(" · deadline ")
        + example(f"next friday · {date_example} · none") + note(" · category ")
        + example("none") + note(" clears"),
        "  " + note("quotes keep shell chars (& ! * ( )) literal; ") + command('jasem todo add "…"')
        + note(" force-adds text that starts with a command word"),

        header("TIME") + note("  ") + command("jasem track …") + note("   duration, date & tag auto-detected"),
        "  " + command('jasem track "') + example("1h45min debugging the parser yesterday, work") + command('"'),
        "  " + command('jasem track "') + example("spent half an hour on emails") + command('"'),
        "  " + note("commas optional; date blank = today, tag blank = work; logging prints the entry id"),
        row("jasem track list", "logged entries  " + note("[period] [tag]")),
        row("jasem track tags", "list categories in use, with counts"),
        row("jasem track report", "totals, by-tag, timeline & top activities  " + note("[period] [tag]")),
        row("jasem track rm <id>…", "delete tracked entries"),
        row("jasem track set <id>", example("time 1h30min · work \"…\" · date yesterday · tag personal")),

        header("SPENDING") + note("  ") + command("jasem acc …") + note("   amount, date & tag auto-detected"),
        "  " + command('jasem acc "') + example("50k lunch with the team yesterday, food") + command('"'),
        "  " + command('jasem acc "') + example("1.5m new phone") + command('"'),
        "  " + note("commas optional; date blank = today, tag blank = general; recording prints the id"),
        row("jasem acc list", "recorded spending  " + note("[period] [tag]")),
        row("jasem acc tags", "list categories in use, with counts"),
        row("jasem acc report", "totals, by-tag, timeline & top spends  " + note("[period] [tag]")),
        row("jasem acc rm <id>…", "delete spending record(s)"),
        row("jasem acc set <id>", example('amount 60k · title "…" · description "…" · date yesterday · tag food')),
        "  " + note("period = ") + example("today · week · month · all")
        + note("  (report defaults to week, list to all)"),

        header("MORE"),
        row("jasem help", "this screen"),
        row("jasem version", "print the installed version  " + note("(--version, -v)")),

        header("AI PARSING") + note("  add, track & acc call a model; pick a backend with JASEM_PROVIDER"),
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
        row("  accent", example(config.accent)
            + note("   (JASEM_ACCENT: a color name or r,g,b)")),
        row("  color", note("auto on a terminal; ") + example("NO_COLOR")
            + note(" forces off, ") + example("FORCE_COLOR") + note(" forces on")),
        row("  env vars", note("JASEM_DIR · JASEM_FILE · JASEM_TRACK_FILE · JASEM_SPEND_FILE · "
                               "JASEM_PROVIDER · JASEM_MODEL · JASEM_API_KEY · "
                               "JASEM_OPENAI_API_BASE · JASEM_API_BASE · OLLAMA_HOST · "
                               "JASEM_JALALI · JASEM_ACCENT")),
    ]
    return "\n".join(sections)
