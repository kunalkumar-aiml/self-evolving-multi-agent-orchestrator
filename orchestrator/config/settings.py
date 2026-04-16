from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeSettings:
    planner_model: str
    coder_model: str
    reviewer_model: str
    benchmark_timeout_seconds: int
    fallback_to_mock: bool
    fallback_warn: bool
    mock_llm: bool

    @staticmethod
    def _as_bool(value: str, default: bool) -> bool:
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "y", "on"}:
            return True
        if normalized in {"0", "false", "no", "n", "off"}:
            return False
        return default

    @classmethod
    def from_env(cls) -> "RuntimeSettings":
        return cls(
            planner_model=os.getenv("ORCHESTRATOR_PLANNER_MODEL", "llama3.1:8b"),
            coder_model=os.getenv("ORCHESTRATOR_CODER_MODEL", "deepseek-coder:6.7b"),
            reviewer_model=os.getenv("ORCHESTRATOR_REVIEWER_MODEL", "llama3.1:8b"),
            benchmark_timeout_seconds=int(os.getenv("ORCHESTRATOR_BENCHMARK_TIMEOUT_SECONDS", "8")),
            fallback_to_mock=cls._as_bool(os.getenv("ORCHESTRATOR_FALLBACK_TO_MOCK", "1"), True),
            fallback_warn=cls._as_bool(os.getenv("ORCHESTRATOR_FALLBACK_WARN", "1"), True),
            mock_llm=cls._as_bool(os.getenv("ORCHESTRATOR_MOCK_LLM", "0"), False),
        )
