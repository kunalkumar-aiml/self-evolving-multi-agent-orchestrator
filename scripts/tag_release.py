from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create and optionally push a release tag")
    parser.add_argument("--version", required=True, help="Version string without v prefix, e.g. 0.1.0")
    parser.add_argument("--push", action="store_true", help="Push tag to origin after creation")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    tag_name = f"v{args.version}"

    exists = run(["git", "tag", "--list", tag_name], cwd=repo_root)
    if exists.returncode != 0:
        print(exists.stderr.strip())
        return 1
    if exists.stdout.strip() == tag_name:
        print(f"Tag already exists: {tag_name}")
        return 1

    create = run(["git", "tag", "-a", tag_name, "-m", f"Release {tag_name}"], cwd=repo_root)
    if create.returncode != 0:
        print(create.stderr.strip())
        return 1

    print(f"Created tag: {tag_name}")

    if args.push:
        push = run(["git", "push", "origin", tag_name], cwd=repo_root)
        if push.returncode != 0:
            print(push.stderr.strip())
            return 1
        print(f"Pushed tag: {tag_name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
