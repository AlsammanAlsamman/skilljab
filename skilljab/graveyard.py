"""Graveyard: past silent failures, keyed by pipeline shape, for deja-vu prompts.

Entry: {"id": "...", "shape": ["clean","fit"], "data_type": "tabular", "stage": "fit",
        "stone": "target_leakage", "failure": "one sentence", "explanation": "why", "domain": "..."}
`search` shows the SETUP of similar cases; the judge/planner must predict the outcome before
it is revealed (predict-then-reveal). Local in v1: <skill_dir>/history/graveyard.json plus the
seed shipped in the package.
"""
from __future__ import annotations
import pathlib, uuid
from .util import read_json, write_json, pkg_path, now

def _seed():
    p = pkg_path("pack", "graveyard", "seed.json")
    return read_json(p)["entries"] if p.exists() else []

def load(local_path=None):
    entries = list(_seed())
    if local_path and pathlib.Path(local_path).exists():
        entries += read_json(local_path).get("entries", [])
    return entries

def add(local_path, entry: dict):
    p = pathlib.Path(local_path)
    g = read_json(p) if p.exists() else {"entries": []}
    entry.setdefault("id", f"g-{uuid.uuid4().hex[:8]}"); entry.setdefault("added", now())
    g["entries"].append(entry); write_json(p, g); return entry

def similarity(shape_a, shape_b):
    a, b = set(map(str.lower, shape_a)), set(map(str.lower, shape_b))
    return len(a & b) / len(a | b) if (a | b) else 0.0

def search(shape, data_type=None, local_path=None, k=5, reveal=False):
    scored = []
    for e in load(local_path):
        s = similarity(shape, e.get("shape", []))
        if data_type and e.get("data_type") and e["data_type"] != data_type: s *= 0.5
        if s > 0: scored.append((s, e))
    scored.sort(key=lambda x: -x[0])
    out = []
    for s, e in scored[:k]:
        setup = {k2: e[k2] for k2 in ("id", "shape", "data_type", "domain", "stage") if k2 in e}
        setup["similarity"] = round(s, 2)
        if reveal:
            setup.update({k2: e[k2] for k2 in ("stone", "failure", "explanation") if k2 in e})
        out.append(setup)
    return out
