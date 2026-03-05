from __future__ import annotations

import os
import sys
from pathlib import Path


def _clean_env_vars() -> None:
    for key in (
        "TCL_LIBRARY",
        "TK_LIBRARY",
        "TCLLIBPATH",
        "PYTHONHOME",
        "PYTHONPATH",
    ):
        os.environ.pop(key, None)


def _sanitize_path() -> None:
    raw = os.environ.get("PATH", "")
    if not raw:
        return

    blocked_tokens = (
        "\\anaconda3\\library\\bin",
        "\\anaconda3\\dlls",
        "\\anaconda3\\libs",
        "\\anaconda3\\envs\\",
    )

    kept: list[str] = []
    for item in raw.split(os.pathsep):
        part = item.strip()
        if not part:
            continue
        lower = part.lower()
        if any(token in lower for token in blocked_tokens):
            continue
        kept.append(part)

    os.environ["PATH"] = os.pathsep.join(kept)


def _set_tk_paths(base: Path) -> None:
    candidates = [
        base,
        base / "_internal",
        Path(getattr(sys, "_MEIPASS", "")),
    ]

    for root in candidates:
        if not str(root):
            continue
        tcl_dir = root / "_tcl_data"
        tk_dir = root / "_tk_data"
        if tcl_dir.is_dir() and tk_dir.is_dir():
            os.environ["TCL_LIBRARY"] = str(tcl_dir)
            os.environ["TK_LIBRARY"] = str(tk_dir)
            os.environ.pop("TCLLIBPATH", None)
            break


def prepare_runtime_env() -> None:
    _clean_env_vars()
    _sanitize_path()

    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        _set_tk_paths(exe_dir)
