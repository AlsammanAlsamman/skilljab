"""Score the judge's lineup picks against planted culprits and keep a calibration log.

lineup.json (written by the judge session, culprit filled in by the engine/user):
  {"round": 3, "plans": ["plan_a","plan_b","plan_c"], "question": "failed|best",
   "judge_pick": "plan_b", "judge_reason": "...", "culprit": "plan_c"|null}
"""
from __future__ import annotations
import pathlib
from .util import read_json, write_json, now

def score(entry: dict) -> dict:
    culprit = entry.get("culprit"); pick = entry.get("judge_pick")
    hit = None if culprit is None else (pick == culprit)
    return {**entry, "hit": hit, "scored": now()}

def append_log(log_path, scored: dict):
    log_path = pathlib.Path(log_path)
    log = read_json(log_path) if log_path.exists() else {"entries": []}
    log["entries"].append(scored); write_json(log_path, log); return log

def stats(log: dict) -> dict:
    e = [x for x in log.get("entries", []) if x.get("hit") is not None]
    hits = sum(1 for x in e if x["hit"])
    return {"n_scored": len(e), "hits": hits, "hit_rate": round(hits / len(e), 3) if e else None,
            "n_unscored": sum(1 for x in log.get("entries", []) if x.get("hit") is None)}
