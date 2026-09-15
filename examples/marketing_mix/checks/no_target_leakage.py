#!/usr/bin/env python3
"""Fires if any non-outcome numeric column in the stage output is suspiciously close to `revenue`
(a leaked/derived copy of the target -- e.g. an ad-platform "attributed_revenue" export column)."""
import sys, json
import pandas as pd

CORR_THRESHOLD = 0.75

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

    if "revenue" not in df.columns:
        print(json.dumps({"fired": False, "message": "no revenue column to check against"}))
        return 0

    numeric = df.select_dtypes("number")
    if "revenue" not in numeric.columns:
        print(json.dumps({"fired": False, "message": "revenue column is not numeric"}))
        return 0

    suspects = []
    for col in numeric.columns:
        if col == "revenue":
            continue
        s = numeric[col]
        if s.nunique(dropna=True) < 2:
            continue
        corr = numeric["revenue"].corr(s)
        if pd.notna(corr) and abs(corr) > CORR_THRESHOLD:
            suspects.append((col, round(float(corr), 4)))

    if suspects:
        cols = ", ".join(f"{c} (corr={v})" for c, v in suspects)
        print(json.dumps({
            "fired": True,
            "message": f"Possible target leakage: {cols} is almost a copy of revenue and will "
                        f"crush the other channel coefficients toward zero. Drop it before fitting."
        }))
        return 1

    print(json.dumps({"fired": False, "message": f"no column correlates with revenue above {CORR_THRESHOLD}"}))
    return 0

if __name__ == "__main__":
    sys.exit(main())
