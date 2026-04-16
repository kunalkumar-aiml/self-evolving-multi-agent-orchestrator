from __future__ import annotations

import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class BenchmarkTask:
    task_id: str
    prompt: str
    function_name: str
    tests: str


@dataclass
class BenchmarkResult:
    compile_ok: bool
    tests_passed: bool
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool = False
    duration_seconds: float = 0.0


def load_humaneval_tasks(file_path: Path) -> list[BenchmarkTask]:
    payload = json.loads(file_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Task file must contain a JSON array.")

    tasks: list[BenchmarkTask] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("Each task must be a JSON object.")
        required = ["task_id", "prompt", "function_name", "tests"]
        missing = [key for key in required if key not in item]
        if missing:
            raise ValueError(f"Task is missing required keys: {missing}")

        tasks.append(
            BenchmarkTask(
                task_id=item["task_id"],
                prompt=item["prompt"],
                function_name=item["function_name"],
                tests=item["tests"],
            )
        )
    return tasks


def evaluate_generated_code(code: str, task: BenchmarkTask, timeout_seconds: int = 8) -> BenchmarkResult:
    script = (
        f"{code}\n\n"
        f"{task.tests}\n\n"
        "if __name__ == '__main__':\n"
        "    _run_tests()\n"
    )

    started = time.monotonic()

    try:
        proc = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        duration = round(time.monotonic() - started, 4)

        compile_ok = proc.returncode == 0
        return BenchmarkResult(
            compile_ok=compile_ok,
            tests_passed=compile_ok,
            stdout=proc.stdout,
            stderr=proc.stderr,
            exit_code=proc.returncode,
            timed_out=False,
            duration_seconds=duration,
        )
    except subprocess.TimeoutExpired as exc:
        duration = round(time.monotonic() - started, 4)
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\nTimed out after {timeout_seconds}s"
        return BenchmarkResult(
            compile_ok=False,
            tests_passed=False,
            stdout=stdout,
            stderr=stderr.strip(),
            exit_code=124,
            timed_out=True,
            duration_seconds=duration,
        )
