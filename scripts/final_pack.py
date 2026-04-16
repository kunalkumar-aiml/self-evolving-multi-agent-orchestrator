from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def run_command(project_root: Path, command: list[str]) -> dict[str, object]:
    proc = subprocess.run(command, cwd=project_root, capture_output=True, text=True)
    return {
        "command": " ".join(command),
        "exit_code": proc.returncode,
        "stdout": (proc.stdout or "").strip(),
        "stderr": (proc.stderr or "").strip(),
    }


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    dist_dir = project_root / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)

    checks = [
        run_command(project_root, [sys.executable, "scripts/run_tests.py"]),
        run_command(project_root, ["npm", "--prefix", "mcp-server", "run", "typecheck"]),
        run_command(project_root, ["npm", "--prefix", "mcp-server", "run", "build"]),
    ]

    manifest = {
        "name": "self-evolving-multi-agent-codebase-orchestrator",
        "version": "0.1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "artifacts": {
            "latest_langgraph_state": "benchmarks/humaneval/results/latest_langgraph_state.json",
            "latest_benchmark_summary": "benchmarks/humaneval/results/latest_summary.json",
        },
        "checks": checks,
    }

    manifest_path = dist_dir / "release_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Saved release manifest to {manifest_path}")

    failed = [check for check in checks if check["exit_code"] != 0]
    if failed:
        print("Final pack completed with failing checks.")
        return 1

    print("Final pack completed successfully ✅")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
