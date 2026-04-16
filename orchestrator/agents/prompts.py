import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class AgentPrompts:
    planner: str
    coder: str
    reviewer: str


def default_prompts() -> AgentPrompts:
    return AgentPrompts(
        planner=(
            "You are the Planner agent. Break the task into actionable coding steps, "
            "constraints, and expected test strategy. Keep output under 8 bullets."
        ),
        coder=(
            "You are the Coder agent. Produce Python code that solves the task exactly. "
            "Return only code in a markdown code block."
        ),
        reviewer=(
            "You are the Reviewer agent. Evaluate correctness, edge cases, and whether the "
            "coder output likely passes tests. Return a concise verdict and specific fixes."
        ),
    )


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_prompt_bank_path() -> Path:
    return _project_root() / "orchestrator" / "config" / "prompt_bank.json"


def prompts_to_dict(prompts: AgentPrompts) -> dict[str, str]:
    return asdict(prompts)


def dict_to_prompts(payload: dict[str, str]) -> AgentPrompts:
    return AgentPrompts(
        planner=payload.get("planner", default_prompts().planner),
        coder=payload.get("coder", default_prompts().coder),
        reviewer=payload.get("reviewer", default_prompts().reviewer),
    )


def load_prompt_bank(path: Path | None = None) -> AgentPrompts:
    target = path or default_prompt_bank_path()
    if not target.exists():
        return default_prompts()
    payload = json.loads(target.read_text(encoding="utf-8"))
    return dict_to_prompts(payload)


def save_prompt_bank(prompts: AgentPrompts, path: Path | None = None) -> None:
    target = path or default_prompt_bank_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(prompts_to_dict(prompts), indent=2), encoding="utf-8")
