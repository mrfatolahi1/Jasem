"""Construction of the colorized ``jasem help`` text."""

from ..shared.calendar_view import CalendarView

WIKI_URL = "https://github.com/mrfatolahi1/Jasem/wiki"
"""Full guide, shown at the top of the help screen."""

WIDTH = 26
"""Left-column width that the command/key descriptions align to."""


def render_help(console, config):
    """Return the full help screen as a single string.

    Args:
        console: Console used to style the text.
        config: Config whose provider, model, and file paths are shown.

    Returns:
        The complete, ready-to-print help text.
    """
    bold, accent = console.bold, console.accent
    command, example, note = console.green, console.yellow, console.dim
    calendar = CalendarView.from_config(config)
    date_example = calendar.format_iso("2026-07-01")

    def header(text):
        """Return a blank-line-separated bold accent section title."""
        return "\n" + bold(accent(text))

    def row(left, right):
        """Return an aligned ``command -> description`` row."""
        return "  " + command(left.ljust(WIDTH)) + right

    def cont(text):
        """Return a wrapped continuation line, aligned under the description column."""
        return " " * (2 + WIDTH) + text

    def tip(text):
        """Return a namespace-level note at the normal indent."""
        return "  " + text

    def example_lines(prefix, *examples):
        """Return ``e.g.`` plus one aligned example per line for a namespace."""
        lines = []
        for index, body in enumerate(examples):
            label = note("e.g.  ") if index == 0 else "      "
            lines.append("    " + label + command(f'{prefix} "') + example(body) + command('"'))
        return lines

    sections = [
        bold("Jasem") + note(" — plain-text task manager, time tracker & spending log · pluggable AI parsing"),
        "",
        bold("Full guide  ") + accent(WIKI_URL),
        "",
        note("Three namespaces, same verbs in each — ") + command("todo") + note(" (tasks) · ")
        + command("track") + note(" (time) · ") + command("acc") + note(" (spending)"),
        note("  verbs:  <text> = add · list · tags · rm · set"),

        header("TASKS"),
        row('jasem todo "<text>"', note("deadline, priority & tags auto-detected")),
        *example_lines("jasem todo",
                       "pay rent next friday, high priority, finance",
                       "review Ali PR by tomorrow, work"),
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
        cont(note("priority ") + example("high·medium·low") + note(" · deadline ")
             + example(f"next friday · {date_example} · none") + note(" · category ") + example("none") + note(" clears")),
        tip(note("quotes keep shell chars (& ! * ( )) literal; ") + command('jasem todo add "…"')
            + note(" force-adds a command-word start")),

        header("TIME"),
        row('jasem track "<text>"', note("duration, date & tag auto-detected")),
        *example_lines("jasem track",
                       "1h45min debugging the parser yesterday, work",
                       "spent half an hour on emails"),
        tip(note("commas optional; date blank = today, tag blank = work; logging prints the entry id")),
        row("jasem track list", "logged entries  " + note("[period] [tag]")),
        row("jasem track tags", "list categories in use, with counts"),
        row("jasem track report", "totals, by-tag, timeline & top activities  " + note("[period] [tag]")),
        row("jasem track rm <id>…", "delete tracked entries"),
        row("jasem track set <id>", example('time 1h30min · work "…" · date yesterday · tag personal')),

        header("SPENDING"),
        row('jasem acc "<text>"', note("amount, date & tag auto-detected")),
        *example_lines("jasem acc",
                       "50k lunch with the team yesterday, food",
                       "1.5m new phone"),
        tip(note("commas optional; date blank = today, tag blank = general; recording prints the id")),
        row("jasem acc list", "recorded spending  " + note("[period] [tag]")),
        row("jasem acc tags", "list categories in use, with counts"),
        row("jasem acc report", "totals, by-tag, timeline & top spends  " + note("[period] [tag]")),
        row("jasem acc rm <id>…", "delete spending record(s)"),
        row("jasem acc set <id>", example('amount 60k · title "…" · description "…" · date yesterday · tag food')),
        tip(note("period = ") + example("today · week · month · all") + note("   (report defaults to week, list to all)")),

        header("MORE"),
        row("jasem  (no args)", "welcome screen"),
        row("jasem --help", "this screen  " + note("(-h)")),
        row("jasem --version", "logo, version & project link  " + note("(-v)")),

        header("AI PARSING"),
        "  " + note("add, track & acc call a model; pick a backend with ") + example("JASEM_PROVIDER"),
        row("ollama  (default)", note("local, no key — run ") + command("ollama serve") + note(" + a small model")),
        row("openai", note("any OpenAI-compatible API — set ") + example("JASEM_API_KEY")),
        cont(note("(+ ") + example("JASEM_OPENAI_API_BASE") + note(" or ") + example("OPENAI_BASE_URL")
             + note(" for non-OpenAI hosts)")),
        row("anthropic", note("Claude — set ") + example("JASEM_PROVIDER=anthropic") + note(" + ") + example("JASEM_API_KEY")),
        tip(note("backend down → entries are still saved (regex dates; track falls back to the comma format)")),

        header("FILES & CONFIG"),
        row("provider", example(config.provider) + note("   (JASEM_PROVIDER: ollama · openai · anthropic)")),
        row("model", example(config.model) + note("   (JASEM_MODEL)")),
        row("tasks", config.task_file + note("  (plain Markdown, hand-editable)")),
        row("time log", config.track_file + note("  (plain Markdown)")),
        row("spending", config.spend_file + note("  (plain Markdown)")),
        row("calendar", example("Jalali" if config.jalali else "Gregorian")
            + note("   (JASEM_JALALI; data on disk stays Gregorian)")),
        row("accent", example(config.accent) + note("   (JASEM_ACCENT: a color name or r,g,b)")),
        row("color", note("auto on a terminal; ") + example("NO_COLOR")
            + note(" forces off, ") + example("FORCE_COLOR") + note(" forces on")),
        row("env vars", note("JASEM_DIR · JASEM_FILE · JASEM_TRACK_FILE · JASEM_SPEND_FILE ·")),
        cont(note("JASEM_PROVIDER · JASEM_MODEL · JASEM_API_KEY · JASEM_OPENAI_API_BASE ·")),
        cont(note("JASEM_API_BASE · OLLAMA_HOST · JASEM_JALALI · JASEM_ACCENT")),
    ]
    return "\n".join(sections)
