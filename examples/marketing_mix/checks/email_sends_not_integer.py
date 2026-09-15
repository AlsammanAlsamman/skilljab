#!/usr/bin/env python3
"""email_sends is a count (thousands of emails sent) and should always be a whole number.
Fires if a meaningful fraction of rows are non-integer -- a sign that continuous measurement
noise/rounding drift (e.g. an ESP's queued-vs-sent reconciliation, a re-estimated send count)
has been mixed into what should be an exact count. This kind of noise on a predictor biases
its regression coefficient toward zero without crashing anything."""
import sys, json
import pandas as pd

COL = "email_sends"
MIN_FRAC_NONINT = 0.05  # a couple of stray non-integers could be rounding artifacts; a lot cannot

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

    if COL not in df.columns:
        print(json.dumps({"fired": False, "message": f"no {COL} column to check"}))
        return 0

    s = df[COL].dropna()
    if len(s) == 0:
        print(json.dumps({"fired": False, "message": f"{COL} is empty"}))
        return 0

    nonint = s[(s - s.round()).abs() > 1e-9]
    frac = len(nonint) / len(s)

    if frac >= MIN_FRAC_NONINT:
        example = round(float(nonint.iloc[0]), 4)
        print(json.dumps({
            "fired": True,
            "message": f"{len(nonint)} of {len(s)} rows ({round(frac*100,1)}%) of {COL} are "
                       f"non-integer (e.g. {example}), but email sends should be a whole count. "
                       f"This looks like measurement noise/rounding drift injected into a count "
                       f"column, which will bias its estimated return-per-dollar toward zero. "
                       f"Investigate the source export for this column."
        }))
        return 1

    print(json.dumps({"fired": False, "message": f"{COL} values are all (near-)integer as expected"}))
    return 0

if __name__ == "__main__":
    sys.exit(main())
