from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from pprint import pprint
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from orchestrator.evaluation.benchmark_runner import load_humaneval_tasks
from orchestrator.langgraph_workflow import run_demo
from orchestrator.agents.prompts import default_prompts, save_prompt_bank


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run HumanEval-style benchmark cycle")
    parser.add_argument("--task-file", default="benchmarks/humaneval/tasks.json")
    parser.add_argument("--max-iterations", type=int, default=2)
    parser.add_argument("--benchmark-timeout", type=int, default=8)
    parser.add_argument("--mcp-enabled", action="store_true")
    parser.add_argument("--summary-file", default="benchmarks/humaneval/results/latest_summary.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    save_prompt_bank(default_prompts())

    tasks_file = PROJECT_ROOT / args.task_file
    tasks = load_humaneval_tasks(tasks_file)

    summary: list[dict[str, object]] = []
    for task in tasks:
        final_state = run_demo(
            task_prompt=task.prompt,
            benchmark_task={
                "task_id": task.task_id,
                "function_name": task.function_name,
                "tests": task.tests,
            },
            max_iterations=args.max_iterations,
            benchmark_timeout_seconds=args.benchmark_timeout,
            mcp_enabled=args.mcp_enabled,
        )
        summary.append(
            {
                "task_id": task.task_id,
                "score": final_state.get("success_score"),
                "tests_passed": final_state.get("latest_run", {}).get("tests_passed"),
                "iteration": final_state.get("iteration"),
                "llm_source": final_state.get("latest_run", {}).get("llm_source"),
                "llm_fallback_reason": final_state.get("latest_run", {}).get("llm_fallback_reason"),
                "timed_out": final_state.get("latest_run", {}).get("timed_out"),
                "duration_seconds": final_state.get("latest_run", {}).get("duration_seconds"),
            }
        )

    print("=== Benchmark Summary ===")
    pprint(summary)

    out_file = PROJECT_ROOT / args.summary_file
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Saved summary to {out_file}")


if __name__ == "__main__":
    if os.getenv("ORCHESTRATOR_MOCK_LLM") is None:
        print("Tip: set ORCHESTRATOR_MOCK_LLM=1 (or configure .env) for deterministic local run without Ollama.")
    main()
