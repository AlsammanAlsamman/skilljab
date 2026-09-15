#!/usr/bin/env python3
"""Fires if a numeric spend/volume column looks like it has two populations of magnitude
(e.g. a subset of rows recorded in raw dollars instead of $k, or units otherwise mismatched
across a batch/region) -- a classic 'two units mixed into one column' data-entry problem.

Scans EVERY path given on the command line (not just argv[1]) and is registered for both the
`prepare` and `fit` checkpoints. Reason: a corruption can be injected into prepared.csv *after*
the `prepare`-stage check already ran (e.g. a stone applied "after_stage: prepare"), in which
case the file the `prepare` checkpoint saw was still clean -- but that same corrupted file is
what `fit` receives as its input, so re-running this scan at the `fit` checkpoint (where it is
argv[2], the stage input) catches it. Checking every argv path makes the script agnostic to
which checkpoint invoked it."""
import sys, json
import pandas as pd

# a "high" value is one that is at least this many times the column's typical (median) value
RATIO_THRESHOLD = 10
# the corrupted subset must be a meaningfully-sized minority, not a couple of legit big weeks
MIN_FRAC = 0.02
MAX_FRAC = 0.45


def scan(df):
    numeric = df.select_dtypes("number")
    suspects = []
    for col in numeric.columns:
        if col == "revenue":
            continue
        s = numeric[col].dropna()
        # skip one-hot / binary dummy columns
        if s.nunique() <= 2:
            continue
        pos = s[s > 0]
        if len(pos) < 20:
            continue
        median = pos.median()
        if median <= 0:
            continue
        high = pos[pos > RATIO_THRESHOLD * median]
        frac_high = len(high) / len(pos)
        if MIN_FRAC <= frac_high <= MAX_FRAC:
            suspects.append((col, round(frac_high, 4), int(len(high)), round(float(median), 2)))
    return suspects


def main():
    paths = [p for p in sys.argv[1:3] if p]
    if not paths:
        print(json.dumps({"fired": False, "message": "no stage files provided"}))
        return 0

    all_suspects = {}
    for path in paths:
        try:
            df = pd.read_csv(path)
        except Exception:
            continue
        for col, frac, n, median in scan(df):
            # keep the strongest (first-seen) finding per column across the files checked
            all_suspects.setdefault(col, (frac, n, median))

    if all_suspects:
        parts = ", ".join(
            f"{c}: {n} rows are >{RATIO_THRESHOLD}x the column median ({m})"
            for c, (f, n, m) in all_suspects.items()
        )
        print(json.dumps({
            "fired": True,
            "message": f"Possible mixed units: {parts}. Looks like a subset of rows were "
                       f"recorded in a different unit/scale (e.g. raw dollars vs $k) and will "
                       f"distort that channel's coefficient. Check the source export for a unit change."
        }))
        return 1

    print(json.dumps({"fired": False, "message": "no column shows a bimodal magnitude split"}))
    return 0

if __name__ == "__main__":
    sys.exit(main())
