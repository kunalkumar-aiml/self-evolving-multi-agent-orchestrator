from __future__ import annotations

from typing import Any

from orchestrator.agents.prompts import AgentPrompts


def compute_success_score(state: dict[str, Any]) -> float:
    run = state.get("latest_run", {})
    tests_passed = bool(run.get("tests_passed", False))
    reviewer_approved = bool(run.get("reviewer_approved", False))
    compile_ok = bool(run.get("compile_ok", False))
    has_nonempty_code = bool(str(state.get("generated_code", "")).strip())

    score = 0.0
    score += 0.5 if tests_passed else 0.0
    score += 0.3 if reviewer_approved else 0.0
    score += 0.2 if compile_ok else 0.0
    if has_nonempty_code:
        score = min(1.0, score + 0.05)
    return round(score, 3)


def _bounded_prompt(base: str, adaptation: str, feedback: str) -> str:
    if "\nMeta-guidance:" in base:
        base = base.split("\nMeta-guidance:", 1)[0].strip()
    compact_feedback = " ".join(feedback.split())[:300]
    return (
        f"{base}\n"
        f"Meta-guidance: {adaptation}\n"
        f"Latest reviewer feedback: {compact_feedback}"
    ).strip()


def evolve_prompts(current: AgentPrompts, score: float, feedback: str) -> AgentPrompts:
    adaptation = (
        "Prioritize precision and explicit validation." if score < 0.6 else "Preserve strategy and improve efficiency."
    )

    planner = _bounded_prompt(current.planner, adaptation, feedback)
    coder = _bounded_prompt(current.coder, adaptation, feedback)
    reviewer = _bounded_prompt(current.reviewer, adaptation, feedback)
    return AgentPrompts(planner=planner, coder=coder, reviewer=reviewer)
