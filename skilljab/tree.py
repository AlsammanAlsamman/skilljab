"""Decision tree with evidence on the edges.

tree.json: {"version": 1, "nodes": [{"id": "ld_pruning_threshold", "branches": [
   {"choice": "r2<0.2", "votes": 2, "plans": ["plan_a","plan_c"], "evidence": [
       {"kind": "stone|lineup|user_recognized|elicited", "round": 3, "summary": "...", "verdict": "silent|caught|harmless|..."}],
    "status": "default|rejected|open"}]}]}
"""
from __future__ import annotations
from .util import read_json, write_json, now

def build(plans: list[dict]) -> dict:
    nodes = {}
    for i, p in enumerate(plans):
        pname = p.get("name", f"plan_{i+1}")
        for d in p.get("decisions", []):
            node = nodes.setdefault(d["id"], {"id": d["id"], "question": d.get("question", d["id"]), "branches": []})
            br = next((b for b in node["branches"] if b["choice"] == str(d.get("choice"))), None)
            if br is None:
                br = {"choice": str(d.get("choice")), "votes": 0, "plans": [], "why": [], "evidence": [], "status": "open"}
                node["branches"].append(br)
            br["votes"] += 1; br["plans"].append(pname)
            if d.get("why"): br["why"].append(d["why"])
    return {"version": 1, "built": now(), "nodes": list(nodes.values())}

def add_evidence(tree: dict, node_id: str, choice: str, evidence: dict, status: str | None = None) -> dict:
    node = next((n for n in tree["nodes"] if n["id"] == node_id), None)
    if node is None:
        node = {"id": node_id, "question": node_id, "branches": []}; tree["nodes"].append(node)
    br = next((b for b in node["branches"] if b["choice"] == choice), None)
    if br is None:
        br = {"choice": choice, "votes": 0, "plans": [], "why": [], "evidence": [], "status": "open"}; node["branches"].append(br)
    evidence.setdefault("added", now())
    br["evidence"].append(evidence)
    if status: br["status"] = status
    return tree

def summary(tree: dict) -> list[str]:
    lines = []
    for n in tree.get("nodes", []):
        lines.append(f"- **{n.get('question', n['id'])}**")
        for b in n["branches"]:
            ev = ", ".join(f"{e.get('kind')}:{e.get('verdict', e.get('summary', ''))[:40]}" for e in b.get("evidence", []))
            lines.append(f"  - `{b['choice']}` — {b['votes']} vote(s), status *{b.get('status','open')}*" + (f"; evidence: {ev}" if ev else ""))
    return lines
