import numpy as np, pandas as pd, pytest
from skilljab.simulate import simulate, GENERATORS
from skilljab import stones as S
from skilljab.inject import make_manifest, apply_manifest, _accepted
from skilljab.util import write_json, read_json

@pytest.mark.parametrize("gen", sorted(GENERATORS))
def test_generators_write_data_and_truth(tmp_path, gen):
    spec = tmp_path / "spec.yaml"
    spec.write_text(f"generator: {gen}\nn: 120\nseed: 1\nfeatures: {{numeric: 3, categorical: 1}}\n")
    csv, truth = simulate(spec, tmp_path / "out", size_mult=2.0)
    df = pd.read_csv(csv)
    assert len(df) == 240 and "y" in df.columns
    assert truth["estimands"] and truth["n"] == 240
    assert (tmp_path / "out" / "truth.json").exists()

def test_simulate_is_deterministic(tmp_path):
    spec = tmp_path / "spec.yaml"; spec.write_text("generator: tabular_regression\nn: 50\nseed: 9\n")
    a, _ = simulate(spec, tmp_path / "a"); b, _ = simulate(spec, tmp_path / "b")
    assert pd.read_csv(a).equals(pd.read_csv(b))

def test_catalog_entries_have_modules_and_required_fields():
    for e in S.catalog():
        for k in ("id", "character", "applies_to", "dose", "symptom", "wakeup_hint"):
            assert k in e, f"{e.get('id')} missing {k}"
        entry, fn = S.get(e["id"]); assert callable(fn)

@pytest.fixture
def df():
    rng = np.random.default_rng(0)
    d = pd.DataFrame(rng.normal(size=(200, 3)), columns=["x1", "x2", "x3"])
    d["cat1"] = rng.choice(["a", "b"], size=200); d["y"] = 0.8 * d.x1 + rng.normal(size=200)
    return d

@pytest.mark.parametrize("sid", [e["id"] for e in S.catalog()])
def test_every_stone_applies_at_low_and_high_dose(df, sid):
    entry, fn = S.get(sid)
    for level in (0.0, 1.0):
        rng = np.random.default_rng(1)
        out, info = fn(df.copy(), rng, **S.sample_dose(entry, rng, level))
        assert isinstance(out, pd.DataFrame) and isinstance(info, dict)
        assert "y" in out.columns

def test_stones_change_the_data(df):
    for sid in ("target_leakage", "outliers", "duplicates", "correlated_block", "mnar_missing", "unit_mix"):
        entry, fn = S.get(sid); rng = np.random.default_rng(2)
        out, _ = fn(df.copy(), rng, **S.sample_dose(entry, rng, 0.8))
        assert not (out.shape == df.shape and out.equals(df)), sid

def test_duplicates_adds_rows_and_mnar_blanks_outcome(df):
    _, dup = S.get("duplicates"); out, info = dup(df.copy(), np.random.default_rng(0), frac=0.25)
    assert len(out) == 250 and info["n_duplicated"] == 50
    _, mnar = S.get("mnar_missing"); out, info = mnar(df.copy(), np.random.default_rng(0), frac=0.1)
    assert out["y"].isna().sum() == 20 and info["col"] == "y"

def test_accepted_filters_unknown_dose_params():
    _, fn = S.get("target_leakage")
    dose, ignored = _accepted(fn, {"noise_sd": 0.1, "col": "x1"})
    assert dose == {"noise_sd": 0.1} and ignored == ["col"]

def test_manifest_and_apply(tmp_path, df):
    df.to_csv(tmp_path / "d.csv", index=False)
    m = make_manifest(["target_leakage", "duplicates"], seed=3, level=0.5)
    assert [x["stone_id"] for x in m] == ["target_leakage", "duplicates"] and all("dose" in x for x in m)
    applied = apply_manifest(tmp_path / "d.csv", tmp_path / "out.csv", m)
    out = pd.read_csv(tmp_path / "out.csv")
    assert len(applied) == 2 and "x_score" in out.columns and len(out) > len(df)
    # entries for a different boundary are not applied here
    m2 = [{"stone_id": "duplicates", "dose": {"frac": 0.5}, "seed": 0, "after_stage": "clean"}]
    assert apply_manifest(tmp_path / "d.csv", tmp_path / "same.csv", m2) == []
    assert pd.read_csv(tmp_path / "same.csv").equals(pd.read_csv(tmp_path / "d.csv"))
