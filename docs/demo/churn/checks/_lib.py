import sys, json, pandas as pd
def load(argv):
    out = pd.read_csv(argv[1]); inp = pd.read_csv(argv[2]) if len(argv) > 2 else None
    return out, inp
def outcome(df):
    for c in ("churned", "y", "outcome", "target", "label"):
        if c in df.columns: return c
    return None
def finish(fired, message):
    print(json.dumps({"fired": bool(fired), "message": message})); sys.exit(1 if fired else 0)
