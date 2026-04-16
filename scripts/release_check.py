from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CheckResult:
    name: str
    command: list[str]
    return_code: int
    output: str


def run_check(project_root: Path, name: str, command: list[str]) -> CheckResult:
    proc = subprocess.run(command, cwd=project_root, capture_output=True, text=True)
    output = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
    return CheckResult(name=name, command=command, return_code=proc.returncode, output=output.strip())


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    checks = [
        ("python-tests", [sys.executable, "scripts/run_tests.py"]),
        ("langgraph-run", [sys.executable, "scripts/run_langgraph.py", "--max-iterations", "2"]),
        ("benchmark-run", [sys.executable, "scripts/run_benchmark_cycle.py", "--max-iterations", "2", "--benchmark-timeout", "8"]),
        ("mcp-typecheck", ["npm", "--prefix", "mcp-server", "run", "typecheck"]),
        ("mcp-build", ["npm", "--prefix", "mcp-server", "run", "build"]),
    ]

    failures: list[CheckResult] = []
    for name, command in checks:
        result = run_check(project_root, name, command)
        print(f"\n=== {name} ===")
        print(" ".join(command))
        print(result.output)
        if result.return_code != 0:
            failures.append(result)

    if failures:
        print("\nRelease check failed:")
        for failure in failures:
            print(f"- {failure.name} (exit={failure.return_code})")
        return 1

    print("\nRelease check passed ✅")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
