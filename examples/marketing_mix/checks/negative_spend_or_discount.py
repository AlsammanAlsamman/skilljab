#!/usr/bin/env python3
"""Every spend/count/discount column in this feed is bounded below at 0 by definition (you
cannot spend negative dollars, send negative emails, or apply a negative discount percentage).
Fires if any of them contains negative values -- a strong, simple signature that something was
added to (or corrupted) a column that should never go below zero: e.g. Gaussian measurement
noise/jitter added to a percentage or count field, or a bad transform/join."""
import sys, json
import pandas as pd

# columns that are structurally non-negative in this domain (see spec.yaml: min 0 for all of these)
NONNEGATIVE_COLS = ["tv_spend", "search_spend", "social_spend", "email_sends", "discount_pct"]

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

    suspects = []
    for col in NONNEGATIVE_COLS:
        if col not in df.columns:
            continue
        s = df[col].dropna()
        neg = s[s < 0]
        if len(neg) > 0:
            suspects.append((col, len(neg), len(s), round(float(neg.min()), 3)))

    if suspects:
        parts = ", ".join(
            f"{c}: {n} of {total} rows are negative (min {m})" for c, n, total, m in suspects
        )
        print(json.dumps({
            "fired": True,
            "message": f"Impossible negative values: {parts}. These columns cannot legitimately "
                       f"go below zero, so this looks like noise/corruption added to the column "
                       f"(e.g. measurement jitter) rather than real data. Investigate the source "
                       f"before fitting -- that channel's coefficient will be biased."
        }))
        return 1

    print(json.dumps({"fired": False, "message": "no negative values in any spend/count/discount column"}))
    return 0

if __name__ == "__main__":
    sys.exit(main())
