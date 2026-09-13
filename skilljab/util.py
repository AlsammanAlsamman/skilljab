from __future__ import annotations
import json, pathlib, datetime
from typing import Any

def read_json(p: str | pathlib.Path) -> Any:
    with open(p) as f:
        return json.load(f)

def write_json(p: str | pathlib.Path, obj: Any) -> None:
    p = pathlib.Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f:
        json.dump(obj, f, indent=2, sort_keys=False, default=_default)
        f.write("\n")

def read_yaml(p: str | pathlib.Path) -> Any:
    import yaml
    with open(p) as f:
        return yaml.safe_load(f)

def write_yaml(p: str | pathlib.Path, obj: Any) -> None:
    import yaml
    p = pathlib.Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f:
        yaml.safe_dump(obj, f, sort_keys=False)

def now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")

def _default(o):
    import numpy as np
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.floating,)): return float(o)
    if isinstance(o, (np.bool_,)): return bool(o)
    if isinstance(o, np.ndarray): return o.tolist()
    if isinstance(o, pathlib.Path): return str(o)
    raise TypeError(f"not serializable: {type(o)}")

def pkg_path(*parts) -> pathlib.Path:
    return pathlib.Path(__file__).parent.joinpath(*parts)
