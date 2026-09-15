#!/usr/bin/env python3
"""Fires if a numeric column (e.g. discount_pct) got mis-typed as text -- typically because a
spreadsheet/CSV export padded the numbers with whitespace, a non-breaking space, a thousands
separator, or a stray sentinel string -- and prepare.py's "one-hot encode every object column"
step exploded it into one dummy column per distinct value instead of keeping it numeric."""
import sys, json, re
import pandas as pd

# a dummy column produced from a numeric field looks like "<original_name>_<number>"
NUMERIC_SUFFIX = re.compile(r"^(?P<base>.+)_[ \t]*-?\d+(\.\d+)?[ \t]*$")
MIN_EXPLODED_SIBLINGS = 5  # a real categorical (region/quarter) never has this many levels

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"fired": False, "message": "no stage output provided"}))
        return 0

    out_path = sys.argv[1]
    try:
        df = pd.read_csv(out_path, nrows=1)
    except Exception as e:
        print(json.dumps({"fired": False, "message": f"could not read stage output: {e}"}))
        return 0

    groups = {}
    for col in df.columns:
        m = NUMERIC_SUFFIX.match(col)
        if m:
            groups.setdefault(m.group("base"), []).append(col)

    exploded = {base: cols for base, cols in groups.items() if len(cols) >= MIN_EXPLODED_SIBLINGS}

    if exploded:
        parts = ", ".join(f"{base} ({len(cols)} dummy columns)" for base, cols in exploded.items())
        print(json.dumps({
            "fired": True,
            "message": f"Looks like a numeric column got one-hot encoded instead of kept numeric: "
                       f"{parts}. This usually means the source values had stray whitespace/non-breaking "
                       f"spaces/sentinel text that made pandas read the column as text (dtype=object). "
                       f"That channel's real coefficient is now missing from the fit. Clean/strip and "
                       f"coerce the column to numeric before one-hot encoding categoricals."
        }))
        return 1

    print(json.dumps({"fired": False, "message": "no numeric-looking column was exploded into dummies"}))
    return 0

if __name__ == "__main__":
    sys.exit(main())
