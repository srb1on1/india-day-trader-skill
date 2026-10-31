"""Small JSON state helpers; all mutable state lives outside the package in trader/."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path.cwd()
TRADER_DIR = ROOT / "trader"


def read_json(path: str | Path, default: Any = None) -> Any:
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read valid JSON from {p}: {exc}") from exc


def write_json(path: str | Path, value: Any) -> Path:
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=p.name + ".", suffix=".tmp", dir=p.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(tmp_name, p)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
    return p


def state_path(name: str) -> Path:
    return TRADER_DIR / "state" / f"{name}.json"
