from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    cmd = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"]
    proc = subprocess.run(cmd, cwd=project_root)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
