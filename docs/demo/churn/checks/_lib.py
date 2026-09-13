import sys, json, pandas as pd
def load(argv):
    """(stage_output, stage_input). A non-CSV output (result.json) yields out=None; use inp then."""
    out = pd.read_csv(argv[1]) if argv[1].endswith(".csv") else None
    inp = pd.read_csv(argv[2]) if len(argv) > 2 else None
    if out is None and inp is not None: out = inp
    return out, inp
def outcome(df):
    for c in ("churned", "y", "outcome", "target", "label"):
        if c in df.columns: return c
    return None
def finish(fired, message):
    print(json.dumps({"fired": bool(fired), "message": message})); sys.exit(1 if fired else 0)
