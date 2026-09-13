"""The Claude Code plugin: manifest, commands, agents, skill, hook."""
import json, pathlib, shutil, subprocess, sys, pytest

PLUGIN = pathlib.Path(__file__).resolve().parent.parent / "plugin"

def _frontmatter(p):
    txt = p.read_text(); assert txt.startswith("---\n"), p
    return txt.split("---\n", 2)[1]

def test_manifest():
    m = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())
    assert m["name"] == "skilljab" and m["version"] and m["description"]

def test_commands_have_description_and_use_cli():
    names = {p.stem for p in (PLUGIN / "commands").glob("*.md")}
    assert names == {"build", "test", "improve", "jab", "recall", "report"}
    for p in (PLUGIN / "commands").glob("*.md"):
        fm = _frontmatter(p); assert "description:" in fm, p
        assert "skilljab" in p.read_text()

def test_agents_are_blind_by_tools():
    agents = {p.stem: _frontmatter(p) for p in (PLUGIN / "agents").glob("*.md")}
    assert set(agents) == {"planner", "judge", "saboteur", "analyst", "explainer"}
    for fm in agents.values(): assert "name:" in fm and "description:" in fm and "tools:" in fm
    assert "Write" not in agents["analyst"] and "Edit" not in agents["analyst"]     # analyst can't tamper
    assert "Write" not in agents["saboteur"]                                          # saboteur only uses the CLI
    body = (PLUGIN / "agents" / "analyst.md").read_text()
    assert "private/" in body and "--reveal" in body                                 # blindness spelled out

def test_core_skill_frontmatter():
    fm = _frontmatter(PLUGIN / "skills" / "skilljab-core" / "SKILL.md")
    assert "name: skilljab-core" in fm and "description:" in fm

def test_hook_wiring_and_handler(tmp_path):
    h = json.loads((PLUGIN / "hooks" / "hooks.json").read_text())
    cmd = h["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
    assert "${CLAUDE_PLUGIN_ROOT}" in cmd and "not_jabbed.py" in cmd
    handler = PLUGIN / "hooks-handlers" / "not_jabbed.py"
    # no skills in cwd -> empty response, never an error
    p = subprocess.run([sys.executable, str(handler)], input=json.dumps({"tool_input": {"command": "python3 x.py"}, "cwd": str(tmp_path)}), capture_output=True, text=True)
    assert p.returncode == 0 and json.loads(p.stdout) == {}
    p = subprocess.run([sys.executable, str(handler)], input="not json", capture_output=True, text=True)
    assert p.returncode == 0 and json.loads(p.stdout) == {}

def test_hook_warns_when_stale(skill, example):
    handler = PLUGIN / "hooks-handlers" / "not_jabbed.py"
    ev = json.dumps({"tool_input": {"command": "python3 fit.py in.csv out.json"}, "cwd": str(example)})
    p = subprocess.run([sys.executable, str(handler)], input=ev, capture_output=True, text=True)
    out = json.loads(p.stdout)
    assert "NOT jabbed" in out["hookSpecificOutput"]["additionalContext"] and "no rounds yet" in out["hookSpecificOutput"]["additionalContext"]

@pytest.mark.skipif(shutil.which("claude") is None, reason="claude CLI not installed")
def test_claude_plugin_validate_strict():
    p = subprocess.run(["claude", "plugin", "validate", str(PLUGIN), "--strict"], capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, p.stdout + p.stderr
