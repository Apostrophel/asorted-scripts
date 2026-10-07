# Weekly plot of worktime

`hours.py` reads a Super Productivity JSON export and shows how the tracked hours compare to a reference of 37.5 h per week and 7.5 h per day.

## Running it

1. In Super Productivity, export your data as JSON and put the file in this folder.
2. Run:

   ```
   python3 hours.py
   ```

Requires Python 3 and `matplotlib` (`pip install matplotlib`).

Each run prints a summary in the terminal, saves the plot to `hours.png` in this folder (overwriting the previous one) and opens it in a window.

## Terminal output

- **Latest week:** hours per day with the difference from 7.5 h, the week total against 37.5 h, and how much is left per remaining workday.
- **Accumulated balance:** total hours worked minus 7.5 h for every Monday–Friday, counted from the Monday of the first tracked week up to and including yesterday. Today is left out, so an unfinished day does not show up as missing hours.

## Plot

- **Weekly panel:** total hours per week against the 37.5 line, each bar labelled with its total and the difference from the reference.
- **Daily panel:** hours per day for the same weeks against the 7.5 line, with weekends shaded and the current week highlighted.

## Options

| Option | Effect |
|---|---|
| `python3 hours.py export.json` | Read a specific export instead of the newest one |
| `--weeks N` | Number of weeks shown in both panels (default 12) |
| `--since YYYY-MM-DD` | Start date for the accumulated balance |
| `--save other.png` | Save the plot somewhere other than `hours.png` |
| `--no-show` | Save the plot without opening a window |
| `--no-plot` | Only print the summary |

The reference values (`WEEK_REF`, `DAY_REF`) are constants at the top of the script.

## Things to know

- **Which file it reads:** the newest `.json` in the script's folder, so you can drop a fresh export there and re-run.
- **What counts:** all tracked time on every task, in every project, including archived tasks. That includes tasks tagged `workout-included`.
- **Which week is "latest":** the week containing the last tracked day in the export, not necessarily today's week.
- **Weekend hours:** they count toward the weekly total and the balance as extra; the 7.5 h reference only applies to Monday–Friday.
- **Days off:** every weekday counts as 7.5 h owed, so holidays, vacation and sick days with nothing tracked show up as missing hours in the balance.
- **Use a fresh export:** the balance runs up to yesterday by your computer's clock, so with an old export the untracked days in between count as missing.
