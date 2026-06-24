"""Aggregation of time-log entries into the numbers a report displays.

Pure functions over :class:`~jasem.domain.time_entry.TimeEntry` lists: no I/O,
no formatting, no color — so the maths can be unit-tested on its own and the
presenter is left to render the resulting :class:`Report`.
"""

import datetime
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field

TOP_ACTIVITIES = 6
DAILY_TIMELINE_MAX = 31
"""Longest span, in days, still drawn one bar per day; longer spans go weekly."""


@dataclass
class Report:
    """The fully aggregated figures behind a single ``jasem report`` run."""

    label: str = ""
    start: str = ""
    end: str = ""
    tag_filter: str = None
    total_minutes: int = 0
    entry_count: int = 0
    active_days: int = 0
    span_days: int = 0
    avg_per_active_day: int = 0
    busiest_day: tuple = None
    by_tag: list = field(default_factory=list)
    top_activities: list = field(default_factory=list)
    timeline: list = field(default_factory=list)
    timeline_unit: str = "day"


def build_report(entries, start, end, today, label, tag_filter=None):
    """Aggregate ``entries`` (already scoped to ``start``..``end``) into a Report.

    Only entries with a parseable, positive duration count toward the totals,
    matching ``jasem track``'s rule that an unreadable duration ``won't count
    toward totals``.

    Args:
        entries: The :class:`TimeEntry` objects falling in the period.
        start: Inclusive ISO start date of the period.
        end: Inclusive ISO end date of the period.
        today: ISO date of the current day (unused by the maths, accepted so the
            caller's date context stays in one place).
        label: Human label for the period, e.g. ``"last 7 days"``.
        tag_filter: The tag the period was filtered by, or ``None``.

    Returns:
        The populated :class:`Report`.
    """
    start_date = datetime.date.fromisoformat(start)
    end_date = datetime.date.fromisoformat(end)
    span_days = (end_date - start_date).days + 1

    total_minutes = 0
    entry_count = 0
    by_tag = defaultdict(int)
    by_day = defaultdict(int)
    activities = {}
    for entry in entries:
        minutes = entry.minutes()
        if minutes <= 0:
            continue
        entry_count += 1
        total_minutes += minutes
        by_tag[entry.tag or "untagged"] += minutes
        by_day[entry.date] += minutes
        key = entry.work.strip().lower()
        bucket = activities.setdefault(key, [entry.work.strip() or "—", 0, 0])
        bucket[1] += minutes
        bucket[2] += 1

    active_days = len(by_day)
    busiest_day = max(by_day.items(), key=lambda kv: kv[1]) if by_day else None
    avg_per_active_day = round(total_minutes / active_days) if active_days else 0

    by_tag_sorted = sorted(by_tag.items(), key=lambda kv: (-kv[1], kv[0]))
    top = sorted(activities.values(), key=lambda v: (-v[1], v[0].lower()))
    top_activities = [(display, minutes, count)
                      for display, minutes, count in top[:TOP_ACTIVITIES]]

    timeline, timeline_unit = _build_timeline(by_day, start_date, end_date, span_days)

    return Report(
        label=label, start=start, end=end, tag_filter=tag_filter,
        total_minutes=total_minutes, entry_count=entry_count,
        active_days=active_days, span_days=span_days,
        avg_per_active_day=avg_per_active_day, busiest_day=busiest_day,
        by_tag=by_tag_sorted, top_activities=top_activities,
        timeline=timeline, timeline_unit=timeline_unit,
    )


def _build_timeline(by_day, start_date, end_date, span_days):
    """Bucket per-day minutes into a chronological, zero-filled timeline.

    One bucket per day for spans up to :data:`DAILY_TIMELINE_MAX`, otherwise one
    bucket per ISO week so a long ``all`` report stays readable.

    Returns:
        A ``(buckets, unit)`` pair where ``buckets`` is ``[(label, minutes)]``
        and ``unit`` is ``"day"`` or ``"week"``.
    """
    if span_days <= DAILY_TIMELINE_MAX:
        buckets = []
        day = start_date
        while day <= end_date:
            buckets.append((day.strftime("%a %m-%d"), by_day.get(day.isoformat(), 0)))
            day += datetime.timedelta(days=1)
        return buckets, "day"

    weeks = OrderedDict()
    monday = start_date - datetime.timedelta(days=start_date.weekday())
    while monday <= end_date:
        weeks[monday] = 0
        monday += datetime.timedelta(days=7)
    for iso, minutes in by_day.items():
        day = datetime.date.fromisoformat(iso)
        week_start = day - datetime.timedelta(days=day.weekday())
        if week_start in weeks:
            weeks[week_start] += minutes
    buckets = [("wk " + week.strftime("%m-%d"), minutes) for week, minutes in weeks.items()]
    return buckets, "week"
