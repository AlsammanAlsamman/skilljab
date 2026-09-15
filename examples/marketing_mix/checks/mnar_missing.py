#!/usr/bin/env python3
"""Fires if missingness in one column is systematically associated with other columns -- e.g.
revenue is only reported for weeks that clear some threshold, or a region withholds an unusually
high/low week's figure. prepare.py silently drops every such row (dropna 'complete weeks only'),
so if the missingness is tied to the true value (or to correlated predictors), the surviving rows
are a non-random, truncated sample and every downstream estimate is biased -- selection bias that
looks like nothing more than 'we have fewer weeks than usual'.

Runs against the RAW stage input (before dropna), since the output of `prepare` has already had
the affected rows silently removed."""
import sys, json
import pandas as pd

MIN_MISSING = 30       # need enough missing rows for a mean-difference test to be meaningful
STD_DIFF_THRESHOLD = 0.5  # standardized mean difference (Cohen's-d-like) between missing/present groups

def main():
    if len(sys.argv) < 3:
        print(json.dumps({"fired": False, "message": "no stage input provided; cannot see pre-dropna missingness"}))
        return 0

    in_path = sys.argv[2]
    try:
        df = pd.read_csv(in_path)
    except Exception as e:
        print(json.dumps({"fired": False, "message": f"could not read stage input: {e}"}))
        return 0

    numeric = df.select_dtypes("number")
    suspects = []
    for col in df.columns:
        n_missing = df[col].isna().sum()
        if n_missing < MIN_MISSING:
            continue
        miss = df[col].isna()
        for other in numeric.columns:
            if other == col:
                continue
            s = numeric[other]
            if s.isna().any():
                continue
            sd = s.std()
            if sd == 0 or pd.isna(sd):
                continue
            diff = (s[miss].mean() - s[~miss].mean()) / sd
            if abs(diff) > STD_DIFF_THRESHOLD:
                suspects.append((col, int(n_missing), len(df), other, round(float(diff), 3)))
                break  # one confirming signal per missing column is enough

    if suspects:
        parts = "; ".join(
            f"{col} ({n}/{total} rows missing) is associated with {other} (std diff {d})"
            for col, n, total, other, d in suspects
        )
        print(json.dumps({
            "fired": True,
            "message": f"Missingness looks non-random: {parts}. Dropping these rows (the "
                       f"pipeline's 'complete weeks only' step) is not a random sample -- it "
                       f"selectively removes weeks with certain characteristics, which biases "
                       f"every downstream estimate. Investigate why these rows are missing "
                       f"before dropping them; consider imputation or a missingness indicator "
                       f"instead of dropna()."
        }))
        return 1

    print(json.dumps({"fired": False, "message": "no evidence of non-random missingness"}))
    return 0

if __name__ == "__main__":
    sys.exit(main())
