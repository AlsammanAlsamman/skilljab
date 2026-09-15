#!/usr/bin/env python3
"""Fires if revenue OR any numeric feature/spend column has a handful of extreme, implausible
values -- e.g. a refund reversal / duplicate transaction batch inflating a week's revenue, or a
campaign budget-cap glitch / currency-conversion slip spiking a spend column for a few weeks --
which a squared-error fit cannot ignore and which drag the channel coefficients around.

Originally only scanned `revenue` (round 4); generalized after round 21 showed the same stone
can land on a feature column (social_spend) instead of the outcome and sail through unnoticed."""
import sys, json
import pandas as pd

# modified z-score (median/MAD based) threshold; standard robust-outlier heuristic
Z_THRESHOLD = 6.0

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"fired": False, "message": "no stage output provided"}))
        return 0

    out_path = sys.argv[1]
    try:
        df = pd.read_csv(out_path)
    except Exception as e:
        print(json.dumps({"fired": False, "message": f"could not read stage output: {e}"}))
        return 0

    numeric = df.select_dtypes("number")
    suspects = []
    for col in numeric.columns:
        s = numeric[col].dropna()
        if len(s) < 10:
            continue
        # skip one-hot / binary dummy columns -- MAD-based z-score is meaningless for {0,1} data
        if s.nunique() <= 2:
            continue

        median = s.median()
        mad = (s - median).abs().median()
        if mad == 0:
            continue

        modified_z = (s - median).abs() / (1.4826 * mad)
        extreme = s[modified_z > Z_THRESHOLD]
        if len(extreme) > 0:
            suspects.append((col, len(extreme), len(s), round(float(median), 1), round(float(extreme.iloc[0]), 1)))

    if suspects:
        parts = "; ".join(
            f"{col}: {n} of {total} rows implausibly far from the rest (median {med}, e.g. {ex})"
            for col, n, total, med, ex in suspects
        )
        print(json.dumps({
            "fired": True,
            "message": f"Extreme outlier weeks detected: {parts}. These look like data errors "
                       f"(duplicate/refund/budget-cap glitch/typo), not real weeks, and a "
                       f"least-squares fit will let them drag the channel coefficients around. "
                       f"Investigate and consider excluding or winsorizing them before fitting."
        }))
        return 1

    print(json.dumps({"fired": False, "message": "no extreme values detected in revenue or any feature column"}))
    return 0

if __name__ == "__main__":
    sys.exit(main())
