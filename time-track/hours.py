#!/usr/bin/env python3
"""Plot weekly and daily hours from a Super Productivity JSON export.

Usage:
    python3 hours.py                 # newest *.json in this folder
    python3 hours.py export.json     # a specific export
    python3 hours.py --weeks 20      # more history in the plots
    python3 hours.py --since 2026-09-01  # start date for the accumulated balance
    python3 hours.py --no-show       # save the plot without opening a window

The plot is saved to hours.png next to this script on every run (--save to change).
"""
import argparse
import json
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

WEEK_REF = 37.5
DAY_REF = 7.5
WORKDAYS = 5  # Mon-Fri carry the daily reference

BLUE = "#2a78d6"
BLUE_LIGHT = "#9ec5f4"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e6e5e1"
SURFACE = "#fcfcfb"


def newest_export():
    files = sorted(Path(__file__).parent.glob("*.json"), key=lambda p: p.stat().st_mtime)
    if not files:
        raise SystemExit("No .json export found next to this script.")
    return files[-1]


def load_daily_hours(path):
    """Return {date: hours}, summed over active and archived tasks."""
    data = json.loads(Path(path).read_text())
    data = data.get("data", data)
    stores = [data.get("task"), *(data.get(k, {}).get("task") for k in ("archiveYoung", "archiveOld"))]

    hours = defaultdict(float)
    for store in stores:
        for task in ((store or {}).get("entities") or {}).values():
            # A parent's time is the sum of its subtasks, so only count leaves.
            if task.get("subTaskIds"):
                continue
            for day, ms in (task.get("timeSpentOnDay") or {}).items():
                hours[date.fromisoformat(day)] += ms / 3_600_000
    if not hours:
        raise SystemExit(f"No tracked time found in {path}.")
    return hours


def monday(d):
    return d - timedelta(days=d.weekday())


def fmt(h):
    """Hours as H:MM."""
    sign = "-" if h < 0 else ""
    minutes = round(abs(h) * 60)
    return f"{sign}{minutes // 60}:{minutes % 60:02d}"


def print_summary(hours, week_start, today):
    days = [week_start + timedelta(days=i) for i in range(7)]
    total = sum(hours.get(d, 0) for d in days)
    diff = total - WEEK_REF

    print(f"\nWeek {week_start.isocalendar().week}  ({week_start:%d %b} - {days[-1]:%d %b %Y})")
    for d in days:
        h = hours.get(d, 0)
        if d.weekday() >= WORKDAYS and not h:
            continue
        ref = DAY_REF if d.weekday() < WORKDAYS else 0
        note = "" if d > today else f"  ({'+' if h >= ref else ''}{fmt(h - ref)})"
        print(f"  {d:%a %d.%m}  {fmt(h):>6}{note}")
    print(f"  {'Total':<9}  {fmt(total):>6}  of {fmt(WEEK_REF)}")

    if diff >= 0:
        print(f"\n  Reference reached: {fmt(diff)} over.\n")
    else:
        left = sum(1 for d in days if d > today and d.weekday() < WORKDAYS)
        hint = f" ({fmt(-diff / left)} per remaining workday)" if left else ""
        print(f"\n  {fmt(-diff)} short of the reference{hint}.\n")


def print_balance(hours, since, today):
    """Accumulated difference to the reference, up to and including yesterday."""
    until = today - timedelta(days=1)
    if until < since:
        print("  No completed days yet for an accumulated balance.\n")
        return
    days = [since + timedelta(days=i) for i in range((until - since).days + 1)]
    worked = sum(hours.get(d, 0) for d in days)
    expected = DAY_REF * sum(1 for d in days if d.weekday() < WORKDAYS)
    diff = worked - expected

    print(f"Accumulated  ({since:%d %b %Y} - {until:%a %d %b %Y}, today excluded)")
    print(f"  Worked     {fmt(worked):>7}")
    print(f"  Reference  {fmt(expected):>7}  ({round(expected / DAY_REF)} workdays x {fmt(DAY_REF)})")
    print(f"  Balance    {('+' if diff >= 0 else '') + fmt(diff):>7}  ({'extra' if diff >= 0 else 'missing'})\n")


def style(ax, title):
    ax.set_title(title, loc="left", fontsize=11, color=INK, pad=10)
    ax.set_facecolor(SURFACE)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=MUTED, length=0, labelsize=9)
    ax.set_ylabel("hours", color=MUTED, fontsize=9)


def reference_line(ax, value):
    ax.axhline(value, color=INK_2, linewidth=1.2, linestyle=(0, (4, 3)), zorder=3)
    ax.annotate(f"reference {value:g} h", xy=(1, value), xycoords=("axes fraction", "data"),
                xytext=(0, 4), textcoords="offset points", ha="right", fontsize=8, color=INK_2)


def plot(hours, latest, today, n_weeks, save, show):
    import matplotlib
    if not show:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    first = max(monday(min(hours)), latest - timedelta(weeks=n_weeks - 1))
    weeks = [first + timedelta(weeks=i) for i in range((latest - first).days // 7 + 1)]
    totals = [sum(hours.get(w + timedelta(days=i), 0) for i in range(7)) for w in weeks]

    fig, (ax_w, ax_d) = plt.subplots(2, 1, figsize=(11, 7.5), facecolor=SURFACE)

    # Weekly totals; the latest week is highlighted, earlier ones recede.
    colors = [BLUE_LIGHT] * (len(weeks) - 1) + [BLUE]
    bars = ax_w.bar(range(len(weeks)), totals, width=0.7, color=colors, zorder=2)
    for bar, total in zip(bars, totals):
        diff = total - WEEK_REF
        ax_w.annotate(f"{fmt(total)}\n{'+' if diff >= 0 else ''}{fmt(diff)}",
                      xy=(bar.get_x() + bar.get_width() / 2, total), xytext=(0, 3),
                      textcoords="offset points", ha="center", va="bottom",
                      fontsize=8, color=INK, linespacing=1.3, zorder=4,
                      bbox=dict(facecolor=SURFACE, edgecolor="none", pad=1.5))
    ax_w.set_xticks(range(len(weeks)))
    ax_w.set_xticklabels([f"W{w.isocalendar().week}\n{w:%d %b}" for w in weeks])
    ax_w.set_ylim(0, max(max(totals), WEEK_REF) * 1.22)
    style(ax_w, "Hours per week (total and difference from reference)")
    reference_line(ax_w, WEEK_REF)

    # Daily hours for the same weeks as above.
    days = [first + timedelta(days=i) for i in range(len(weeks) * 7)]
    values = [hours.get(d, 0) for d in days]
    colors = [BLUE if d >= latest else BLUE_LIGHT for d in days]
    ax_d.bar(range(len(days)), values, width=0.7, color=colors, zorder=2)
    for i, (d, v) in enumerate(zip(days, values)):
        if d >= latest and v:
            ax_d.annotate(fmt(v), xy=(i, v), xytext=(0, 3), textcoords="offset points",
                          ha="center", va="bottom", fontsize=8, color=INK)
        if d.weekday() == 0 and i:
            ax_d.axvline(i - 0.5, color=GRID, linewidth=1, zorder=1)
        if d.weekday() >= WORKDAYS:
            ax_d.axvspan(i - 0.5, i + 0.5, color=GRID, alpha=0.45, linewidth=0, zorder=0)
    ax_d.set_xticks(range(len(days)))
    letters = len(weeks) <= 8  # day letters get too cramped beyond that
    ax_d.set_xticklabels([(f"{d:%a}"[0] if letters else "") + (f"\n{d:%d %b}" if d.weekday() == 0 else "")
                          for d in days])
    ax_d.set_xlim(-0.6, len(days) - 0.4)
    ax_d.set_ylim(0, max(max(values), DAY_REF) * 1.18)
    style(ax_d, "Hours per day (weekends shaded)")
    reference_line(ax_d, DAY_REF)

    fig.tight_layout(h_pad=2.5)
    fig.savefig(save, dpi=150)
    print(f"Saved plot to {save}")
    if show:
        plt.show()


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("export", nargs="?", help="Super Productivity JSON export (default: newest in this folder)")
    parser.add_argument("--weeks", type=int, default=12, help="weeks shown in the plots (default: 12)")
    parser.add_argument("--since", type=date.fromisoformat, metavar="YYYY-MM-DD",
                        help="start of the accumulated balance (default: Monday of the first tracked week)")
    parser.add_argument("--save", metavar="PNG", default=Path(__file__).parent / "hours.png",
                        help="where to save the plot (default: hours.png next to this script)")
    parser.add_argument("--no-show", action="store_true", help="save the plot without opening a window")
    parser.add_argument("--no-plot", action="store_true", help="only print the summary")
    args = parser.parse_args()

    path = args.export or newest_export()
    print(f"Reading {path}")
    hours = load_daily_hours(path)

    today = date.today()
    latest = monday(max(hours))  # the week of the last tracked day
    print_summary(hours, latest, today)
    # Default to the Monday of the first tracked week, so the balance matches the weekly plot.
    print_balance(hours, args.since or monday(min(hours)), today)
    if not args.no_plot:
        plot(hours, latest, today, max(args.weeks, 1), args.save, not args.no_show)


if __name__ == "__main__":
    main()
