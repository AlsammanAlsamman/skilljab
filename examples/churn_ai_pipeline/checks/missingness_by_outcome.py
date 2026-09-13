#!/usr/bin/env python3
"""Antibody: rows dropped by dropna are not a random sample — missingness depends on the outcome
(e.g. support history purged when an account closes). Compares the INPUT's missingness rate per
column between outcome classes, and the fraction of rows the stage removed."""
import sys
sys.path.insert(0, __import__("os").path.dirname(__file__)); from _lib import load, outcome, finish
out, inp = load(sys.argv)
if inp is None: finish(False, "no input to compare")
y = outcome(inp); msgs = []
dropped = 1 - len(out) / max(1, len(inp))
if dropped > 0.05: msgs.append(f"{dropped:.0%} of rows removed")
if y is not None and inp[y].notna().all():
    for c in inp.columns:
        if c == y: continue
        m = inp[c].isna()
        if m.sum() == 0: continue
        r1, r0 = m[inp[y] == 1].mean(), m[inp[y] == 0].mean()
        if abs(r1 - r0) > 0.05 or (min(r1, r0) > 0 and max(r1, r0) / min(r1, r0) > 2) or (min(r1, r0) == 0 and max(r1, r0) > 0.02):
            msgs.append(f"{c} missing in {r1:.0%} of outcome=1 vs {r0:.0%} of outcome=0")
elif y is not None: msgs.append("the outcome itself has missing values")
finish(msgs, "missingness depends on the outcome — dropna biases the model: " + "; ".join(msgs) if msgs else "ok")
