import pathlib, shutil, pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXAMPLE = ROOT / "examples" / "toy_regression"

@pytest.fixture
def example(tmp_path):
    """A fresh copy of the toy pipeline in a temp dir (no generated state)."""
    dst = tmp_path / "toy"
    shutil.copytree(EXAMPLE, dst, ignore=shutil.ignore_patterns(".claude", "__pycache__"))
    return dst

@pytest.fixture
def skill(example):
    """Initialised + baselined skill dir for the toy pipeline (small sizes for speed)."""
    from skilljab import project as P
    d = P.init("toy", example / "pipeline.yaml", example / ".claude/skills/toy", spec=example / "spec.yaml")
    r = P.baseline(d, sizes=[1, 2], target_n=50000)
    assert r["baseline"]["class"] == "harmless"
    return d
