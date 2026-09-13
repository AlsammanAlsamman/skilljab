#!/usr/bin/env python3
"""PreToolUse hook: when a Bash command looks like it runs a jabbed pipeline for real, warn if
the skill is stale (pipeline changed since baseline, or last round not clean). Never blocks."""
import json, sys, subprocess, pathlib, re

def main():
    try:
        event = json.load(sys.stdin)
    except Exception:
        print(json.dumps({})); return
    cmd = (event.get("tool_input") or {}).get("command", "") or ""
    if not cmd or "skilljab" in cmd:
        print(json.dumps({})); return
    cwd = pathlib.Path(event.get("cwd") or ".")
    skills = [p.parent for p in cwd.glob(".claude/skills/*/antibodies.json")]
    if not skills:
        print(json.dumps({})); return
    notes = []
    for sd in skills:
        try:
            st = json.loads((sd / "history" / "state.json").read_text())
        except Exception:
            continue
        pipe = st.get("pipeline_yaml", "")
        pdir = pathlib.Path(pipe).parent
        # does the command mention a script from the pipeline dir, or the pipeline name?
        mentions = st.get("name", "") in cmd or any(str(f.name) in cmd for f in pdir.glob("*") if f.is_file() and f.suffix in (".py", ".R", ".sh", ".yaml", ".smk", ".nf"))
        if not mentions:
            continue
        try:
            out = subprocess.run([sys.executable, "-m", "skilljab.cli", "status", "--skill", str(sd)], capture_output=True, text=True, timeout=20)
            s = json.loads(out.stdout or "{}")
        except Exception:
            continue
        if not s.get("jabbed"):
            notes.append(f"SkillJab: pipeline '{s.get('name', sd.name)}' is NOT jabbed ({s.get('reason')}). Consider /skilljab:test before a real run.")
    if notes:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": " ".join(notes)}}))
    else:
        print(json.dumps({}))

if __name__ == "__main__":
    main()
