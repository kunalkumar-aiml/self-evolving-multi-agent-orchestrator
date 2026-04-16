from __future__ import annotations

import argparse
import json
from pathlib import Path
from pprint import pprint
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from orchestrator.langgraph_workflow import run_demo


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run self-evolving LangGraph workflow")
    parser.add_argument("--task-prompt", default="Implement add(a, b) returning integer sum")
    parser.add_argument("--max-iterations", type=int, default=3)
    parser.add_argument("--mcp-enabled", action="store_true")
    parser.add_argument("--mcp-target-file", default="")
    parser.add_argument(
        "--output-json",
        default="benchmarks/humaneval/results/latest_langgraph_state.json",
        help="Path (relative to project root) for writing final state JSON",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    result = run_demo(
        task_prompt=args.task_prompt,
        max_iterations=args.max_iterations,
        mcp_enabled=args.mcp_enabled,
        mcp_target_file=args.mcp_target_file,
    )

    print("=== Final State ===")
    pprint(result)
    print("=== Trace Length ===")
    print(len(result.get("trace", [])))

    output_path = PROJECT_ROOT / args.output_json
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Saved final state to {output_path}")
