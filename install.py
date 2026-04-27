"""
Run once to configure FocusCapsule:
  python install.py

Writes the path of the current pythonw.exe to .python-path so that
focuscapsule.vbs can launch the app without a console window.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def find_pythonw() -> Path:
    python = Path(sys.executable)
    # Prefer pythonw.exe (no console) next to the current python.exe
    pythonw = python.with_name("pythonw.exe")
    if pythonw.exists():
        return pythonw
    return python


def install_deps() -> None:
    req = HERE / "requirements.txt"
    if req.exists():
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(req)])


def write_python_path(pythonw: Path) -> None:
    dest = HERE / ".python-path"
    dest.write_text(str(pythonw), encoding="utf-8")
    print(f"Wrote: {dest}")


if __name__ == "__main__":
    print("Installing dependencies...")
    install_deps()
    pythonw = find_pythonw()
    write_python_path(pythonw)
    print(f"Python: {pythonw}")
    print("Done. Double-click focuscapsule.vbs to launch.")
