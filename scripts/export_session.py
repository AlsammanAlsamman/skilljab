#!/usr/bin/env python3
"""Export a Claude Code session transcript to docs/sessions/ as Markdown (+ raw JSONL copy).

Usage: scripts/export_session.py [session.jsonl] [name]
Defaults: newest .jsonl for this project, name = <date>-session.
"""
import json, re, sys, shutil, datetime, pathlib

repo = pathlib.Path(__file__).resolve().parent.parent
proj = pathlib.Path.home() / '.claude/projects' / str(repo).replace('/', '-')
src = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else max(proj.glob('*.jsonl'), key=lambda p: p.stat().st_mtime)
name = sys.argv[2] if len(sys.argv) > 2 else datetime.date.today().isoformat() + '-session'
outdir = pathlib.Path(__file__).resolve().parent.parent / 'docs/sessions'
outdir.mkdir(parents=True, exist_ok=True)

md = outdir / f'{name}.md'
n = 0
with md.open('w') as out:
    out.write(f'# Session transcript — {name}\n\nRaw export of a Claude Code session (`{src.name}`). Curated summary lives in `docs/DESIGN.md`.\n\n---\n\n')
    for line in src.open():
        try: d = json.loads(line)
        except json.JSONDecodeError: continue
        if d.get('type') not in ('user', 'assistant'): continue
        c = d.get('message', {}).get('content')
        parts = [c] if isinstance(c, str) else [x['text'] for x in c or [] if x.get('type') == 'text' and x.get('text', '').strip()]
        text = re.sub(r'<system-reminder>.*?</system-reminder>', '', '\n\n'.join(parts), flags=re.S).strip()
        if not text: continue
        out.write(f"{'**User**' if d['type'] == 'user' else '**Claude**'}\n\n{text}\n\n---\n\n"); n += 1
shutil.copy(src, outdir / f'{name}.raw.jsonl')
print(f'{n} turns → {md}')
