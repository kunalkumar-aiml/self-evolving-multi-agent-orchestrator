from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Literal, TypedDict

from langgraph.graph import END, StateGraph

from orchestrator.agents.prompts import AgentPrompts, load_prompt_bank, prompts_to_dict, save_prompt_bank
from orchestrator.evaluation.benchmark_runner import BenchmarkResult, BenchmarkTask, evaluate_generated_code
from orchestrator.evaluation.meta_evaluator import compute_success_score, evolve_prompts
from orchestrator.config.settings import RuntimeSettings
from orchestrator.llm.ollama_client import OllamaClient
from orchestrator.tools.mcp_stdio_client import MCPClientConfig, MCPStdioClient, default_mcp_server_entry


class OrchestratorState(TypedDict, total=False):
    task_id: str
    task_prompt: str
    iteration: int
    max_iterations: int
    planner_model: str
    coder_model: str
    reviewer_model: str
    mcp_enabled: bool
    mcp_server_entry: str
    mcp_workspace_root: str
    mcp_target_file: str
    benchmark_task: dict[str, str]
    benchmark_timeout_seconds: int
    plan: str
    generated_code: str
    review_notes: str
    latest_run: dict[str, Any]
    success_score: float
    prompt_bank: dict[str, str]
    trace: list[dict[str, Any]]
    should_stop: bool


def _extract_code_block(text: str) -> str:
    match = re.search(r"```(?:python)?\n(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text.strip()


def _parse_reviewer_output(text: str) -> tuple[bool, str]:
    lowered = text.lower()
    approved = "approved" in lowered and "not approved" not in lowered
    if "verdict: reject" in lowered:
        approved = False
    return approved, text.strip()


def _run_result_to_dict(result: BenchmarkResult) -> dict[str, Any]:
    return {
        "compile_ok": result.compile_ok,
        "tests_passed": result.tests_passed,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "exit_code": result.exit_code,
        "timed_out": result.timed_out,
        "duration_seconds": result.duration_seconds,
    }


def _project_root() -> str:
    return str(Path(__file__).resolve().parents[1])


def _mcp_write_and_status(state: OrchestratorState, generated_code: str) -> dict[str, Any]:
    workspace_root = state.get("mcp_workspace_root", _project_root())
    mcp_server_entry = state.get("mcp_server_entry", default_mcp_server_entry(workspace_root))
    target_file = state.get("mcp_target_file", "").strip()

    response: dict[str, Any] = {
        "mcp_enabled": True,
        "mcp_server_entry": mcp_server_entry,
        "mcp_workspace_root": workspace_root,
    }

    with MCPStdioClient(MCPClientConfig(server_entry=mcp_server_entry, workspace_root=workspace_root)) as mcp:
        tools = mcp.list_tools()
        response["mcp_tools"] = [tool.get("name") for tool in tools if isinstance(tool, dict)]

        if target_file:
            write_result = mcp.call_tool(
                "write_file",
                {
                    "path": target_file,
                    "content": f"{generated_code}\n",
                },
            )
            response["mcp_write_result"] = write_result
            response["mcp_target_file"] = target_file

        git_status = mcp.call_tool("git_status", {})
        response["mcp_git_status"] = git_status

    return response


def planner_node(state: OrchestratorState) -> OrchestratorState:
    prompt_bank = state.get("prompt_bank", prompts_to_dict(load_prompt_bank()))
    task_prompt = state.get("task_prompt", "")
    task = state.get("benchmark_task", {})
    iteration = state.get("iteration", 0)
    llm = OllamaClient()
    planner_model = state.get("planner_model", "llama3.1:8b")

    planner_input = (
        f"Iteration: {iteration}\n"
        f"Task prompt: {task_prompt}\n"
        f"Function target: {task.get('function_name', '')}\n"
        "Return a concise execution plan for solving and validating this task."
    )
    plan = llm.chat(
        model=planner_model,
        system_prompt=prompt_bank.get("planner", ""),
        user_prompt=planner_input,
        temperature=0.1,
    )

    trace = state.get("trace", [])
    trace.append(
        {
            "node": "planner",
            "plan": plan,
            "planner_prompt": prompt_bank.get("planner", ""),
            "llm_source": llm.last_response_source,
            "llm_fallback_reason": llm.last_fallback_reason,
        }
    )

    return {
        **state,
        "plan": plan,
        "trace": trace,
    }


def coder_node(state: OrchestratorState) -> OrchestratorState:
    prompt_bank = state.get("prompt_bank", prompts_to_dict(load_prompt_bank()))
    llm = OllamaClient()
    coder_model = state.get("coder_model", "deepseek-coder:6.7b")
    plan = state.get("plan", "")
    task_prompt = state.get("task_prompt", "")
    benchmark_task = state.get("benchmark_task", {})

    coder_input = (
        f"Task: {task_prompt}\n"
        f"Function name: {benchmark_task.get('function_name', '')}\n"
        f"Plan:\n{plan}\n"
        "Generate only valid Python function implementation. Do not include tests."
    )
    raw_code = llm.chat(
        model=coder_model,
        system_prompt=prompt_bank.get("coder", ""),
        user_prompt=coder_input,
        temperature=0.1,
    )
    generated_code = _extract_code_block(raw_code)

    eval_task = BenchmarkTask(
        task_id=str(benchmark_task.get("task_id", state.get("task_id", "unknown-task"))),
        prompt=task_prompt,
        function_name=str(benchmark_task.get("function_name", "")),
        tests=str(benchmark_task.get("tests", "")),
    )
    timeout_seconds = int(state.get("benchmark_timeout_seconds", 8))
    result = evaluate_generated_code(generated_code, eval_task, timeout_seconds=timeout_seconds)

    latest_run = _run_result_to_dict(result)
    latest_run["reviewer_approved"] = False
    latest_run["llm_source"] = llm.last_response_source
    latest_run["llm_fallback_reason"] = llm.last_fallback_reason

    if state.get("mcp_enabled", False):
        try:
            latest_run.update(_mcp_write_and_status(state, generated_code))
        except Exception as exc:
            latest_run["mcp_error"] = str(exc)

    trace = state.get("trace", [])
    trace.append(
        {
            "node": "coder",
            "generated_code": generated_code,
            "coder_prompt": prompt_bank.get("coder", ""),
            "llm_source": llm.last_response_source,
            "llm_fallback_reason": llm.last_fallback_reason,
            "eval": latest_run,
        }
    )

    return {
        **state,
        "generated_code": generated_code,
        "latest_run": latest_run,
        "trace": trace,
    }


def reviewer_node(state: OrchestratorState) -> OrchestratorState:
    prompt_bank = state.get("prompt_bank", prompts_to_dict(load_prompt_bank()))
    llm = OllamaClient()
    reviewer_model = state.get("reviewer_model", "llama3.1:8b")
    run = state.get("latest_run", {})
    generated_code = state.get("generated_code", "")

    reviewer_input = (
        "Review this candidate implementation and benchmark outcome.\n"
        f"Code:\n```python\n{generated_code}\n```\n"
        f"Benchmark result JSON:\n{json.dumps(run, indent=2)}\n"
        "Return:\n"
        "- Verdict: APPROVED or REJECT\n"
        "- A short explanation\n"
        "- Top 2 fixes if rejected"
    )
    raw_review = llm.chat(
        model=reviewer_model,
        system_prompt=prompt_bank.get("reviewer", ""),
        user_prompt=reviewer_input,
        temperature=0.1,
    )
    model_approved, review_notes = _parse_reviewer_output(raw_review)

    updated_run = {
        **run,
        "reviewer_approved": bool(run.get("compile_ok", False)) and bool(run.get("tests_passed", False)) and model_approved,
    }

    trace = state.get("trace", [])
    trace.append(
        {
            "node": "reviewer",
            "review_notes": review_notes,
            "reviewer_prompt": prompt_bank.get("reviewer", ""),
            "llm_source": llm.last_response_source,
            "llm_fallback_reason": llm.last_fallback_reason,
        }
    )

    return {
        **state,
        "review_notes": review_notes,
        "latest_run": updated_run,
        "trace": trace,
    }


def meta_agent_node(state: OrchestratorState) -> OrchestratorState:
    iteration = state.get("iteration", 0)
    max_iterations = state.get("max_iterations", 3)

    baseline_prompts = load_prompt_bank()
    active_prompts = AgentPrompts(**state.get("prompt_bank", prompts_to_dict(baseline_prompts)))

    score = compute_success_score(state)
    feedback = state.get("review_notes", "")
    evolved = evolve_prompts(active_prompts, score=score, feedback=feedback)

    should_stop = score >= 0.95 or iteration + 1 >= max_iterations

    trace = state.get("trace", [])
    trace.append(
        {
            "node": "meta_agent",
            "score": score,
            "iteration": iteration,
            "should_stop": should_stop,
        }
    )

    return {
        **state,
        "iteration": iteration + 1,
        "success_score": score,
        "prompt_bank": prompts_to_dict(evolved),
        "should_stop": should_stop,
        "trace": trace,
    }


def route_after_meta(state: OrchestratorState) -> Literal["planner", "end"]:
    return "end" if state.get("should_stop", False) else "planner"


def build_graph():
    graph = StateGraph(OrchestratorState)

    graph.add_node("planner", planner_node)
    graph.add_node("coder", coder_node)
    graph.add_node("reviewer", reviewer_node)
    graph.add_node("meta_agent", meta_agent_node)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "coder")
    graph.add_edge("coder", "reviewer")
    graph.add_edge("reviewer", "meta_agent")
    graph.add_conditional_edges(
        "meta_agent",
        route_after_meta,
        {
            "planner": "planner",
            "end": END,
        },
    )

    return graph.compile()


def run_demo(
    task_prompt: str = "Implement add(a, b) returning integer sum",
    benchmark_task: dict[str, str] | None = None,
    max_iterations: int = 3,
    mcp_enabled: bool = False,
    mcp_target_file: str = "",
    benchmark_timeout_seconds: int = 8,
) -> OrchestratorState:
    if benchmark_task is None:
        benchmark_task = {
            "task_id": "demo-add",
            "function_name": "add",
            "tests": (
                "def _run_tests():\n"
                "    assert add(1, 2) == 3\n"
                "    assert add(-1, 1) == 0\n"
                "    assert add(0, 0) == 0\n"
            ),
        }

    app = build_graph()
    runtime = RuntimeSettings.from_env()
    planner_model = runtime.planner_model
    coder_model = runtime.coder_model
    reviewer_model = runtime.reviewer_model
    timeout_from_env = runtime.benchmark_timeout_seconds if runtime.benchmark_timeout_seconds > 0 else benchmark_timeout_seconds

    initial_state: OrchestratorState = {
        "task_id": benchmark_task["task_id"],
        "task_prompt": task_prompt,
        "iteration": 0,
        "max_iterations": max_iterations,
        "planner_model": planner_model,
        "coder_model": coder_model,
        "reviewer_model": reviewer_model,
        "mcp_enabled": mcp_enabled,
        "mcp_workspace_root": _project_root(),
        "mcp_server_entry": default_mcp_server_entry(_project_root()),
        "mcp_target_file": mcp_target_file,
        "benchmark_task": benchmark_task,
        "benchmark_timeout_seconds": timeout_from_env,
        "prompt_bank": prompts_to_dict(load_prompt_bank()),
        "trace": [],
    }
    result = app.invoke(initial_state)
    latest_prompt_bank = result.get("prompt_bank", {})
    if isinstance(latest_prompt_bank, dict):
        save_prompt_bank(AgentPrompts(**latest_prompt_bank))
    return result
