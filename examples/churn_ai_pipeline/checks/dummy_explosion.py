#!/usr/bin/env python3
"""Antibody: a numeric column arrived as text (spreadsheet export: '1,234', ' 12 ', 'NA') and
get_dummies one-hot encoded every distinct value. Fires when one prefix spawned > 20 dummy columns
or the prepared table has > 4x the input's columns."""
import sys, re, collections
sys.path.insert(0, __import__("os").path.dirname(__file__)); from _lib import load, finish
out, inp = load(sys.argv)
prefix = collections.Counter(re.split(r"_(?=[^_]*$)", c)[0] for c in out.columns if "_" in c)
big = {p: n for p, n in prefix.items() if n > 20}
ratio = len(out.columns) / max(1, len(inp.columns)) if inp is not None else 1
fired = bool(big) or ratio > 4
finish(fired, f"one-hot explosion: {big or ''} columns {len(inp.columns) if inp is not None else '?'} -> {len(out.columns)}; a numeric column was probably text" if fired else "ok")
