"""PyInstaller runtime hook: lock Tcl/Tk to bundled runtime."""

from __future__ import annotations

import os
import sys
from pathlib import Path


for key in ("TCL_LIBRARY", "TK_LIBRARY", "TCLLIBPATH", "PYTHONHOME", "PYTHONPATH"):
    os.environ.pop(key, None)

base = Path(getattr(sys, "_MEIPASS", ""))
if base:
    tcl_dir = base / "_tcl_data"
    tk_dir = base / "_tk_data"
    if tcl_dir.is_dir() and tk_dir.is_dir():
        os.environ["TCL_LIBRARY"] = str(tcl_dir)
        os.environ["TK_LIBRARY"] = str(tk_dir)

# Filter out known conda/global python dll locations that can hijack tcl/tk dll loading.
raw_path = os.environ.get("PATH", "")
if raw_path:
    blocked_tokens = (
        "\\anaconda3\\library\\bin",
        "\\anaconda3\\dlls",
        "\\anaconda3\\libs",
        "\\anaconda3\\envs\\",
    )
    parts = []
    for item in raw_path.split(os.pathsep):
        s = item.strip()
        if not s:
            continue
        lower = s.lower()
        if any(token in lower for token in blocked_tokens):
            continue
        parts.append(s)

    # Keep bundled directory at the front.
    if str(base):
        parts.insert(0, str(base))
    os.environ["PATH"] = os.pathsep.join(dict.fromkeys(parts))
