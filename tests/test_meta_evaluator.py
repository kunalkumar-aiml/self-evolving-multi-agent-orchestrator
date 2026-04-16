from __future__ import annotations

from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from orchestrator.agents.prompts import AgentPrompts
from orchestrator.evaluation.meta_evaluator import compute_success_score, evolve_prompts


class MetaEvaluatorTests(unittest.TestCase):
    def test_score_uses_run_signals(self) -> None:
        state = {
            "generated_code": "def add(a,b): return a+b",
            "latest_run": {
                "compile_ok": True,
                "tests_passed": True,
                "reviewer_approved": True,
            },
        }
        score = compute_success_score(state)
        self.assertEqual(score, 1.0)

    def test_prompt_evolution_does_not_bloat(self) -> None:
        prompts = AgentPrompts(
            planner="Planner base\nMeta-guidance: old\nLatest reviewer feedback: old",
            coder="Coder base",
            reviewer="Reviewer base",
        )

        evolved = evolve_prompts(prompts, score=0.1, feedback="Need edge-case checks")

        self.assertIn("Meta-guidance", evolved.planner)
        self.assertNotIn("old\nLatest reviewer feedback: old\nMeta-guidance", evolved.planner)
        self.assertIn("Need edge-case checks", evolved.planner)


if __name__ == "__main__":
    unittest.main()
