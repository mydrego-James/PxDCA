"""Cross-platform local installer for PxDCA."""

from __future__ import annotations

import subprocess
import shutil
import sys
import venv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VENV = ROOT / ".venv"


def _venv_python() -> Path:
    if sys.platform == "win32":
        return VENV / "Scripts" / "python.exe"
    return VENV / "bin" / "python"


def main() -> int:
    if not ((3, 12) <= sys.version_info[:2] < (3, 14)):
        print("[ERROR] PxDCA requires Python 3.12 or 3.13.", file=sys.stderr)
        return 1

    print(f"[PxDCA] Using Python {sys.version.split()[0]} from {sys.executable}")
    if _venv_python().exists():
        probe = subprocess.run(
            [str(_venv_python()), "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"],
            capture_output=True,
            text=True,
        )
        expected = f"{sys.version_info.major}.{sys.version_info.minor}"
        if probe.returncode != 0 or probe.stdout.strip() != expected:
            print(f"[PxDCA] Recreating .venv for Python {expected}...")
            shutil.rmtree(VENV)
    if not _venv_python().exists():
        print("[PxDCA] Creating .venv...")
        venv.EnvBuilder(with_pip=True).create(VENV)

    python = str(_venv_python())
    subprocess.run([python, "-m", "pip", "install", "--upgrade", "pip"], check=True)
    subprocess.run(
        [python, "-m", "pip", "install", "-r", str(ROOT / "requirements.txt")],
        check=True,
    )
    subprocess.run(
        [
            python,
            "-c",
            (
                "import fastmcp, sys; "
                "assert fastmcp.__version__.split('.')[0] == '3'; "
                "assert (3, 12) <= sys.version_info[:2] < (3, 14)"
            ),
        ],
        cwd=ROOT,
        check=True,
    )
    subprocess.run([python, "-m", "compileall", "-q", "server"], cwd=ROOT, check=True)
    print("[PxDCA] Local installation completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
