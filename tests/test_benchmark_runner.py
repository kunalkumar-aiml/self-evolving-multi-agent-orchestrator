from __future__ import annotations

from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from orchestrator.evaluation.benchmark_runner import BenchmarkTask, evaluate_generated_code


class BenchmarkRunnerTests(unittest.TestCase):
    def test_timeout_is_captured_without_crash(self) -> None:
        task = BenchmarkTask(
            task_id="timeout-case",
            prompt="Create a function that loops forever",
            function_name="spin",
            tests="def _run_tests():\n    spin()",
        )
        code = "def spin():\n    while True:\n        pass"

        result = evaluate_generated_code(code, task, timeout_seconds=1)

        self.assertFalse(result.compile_ok)
        self.assertFalse(result.tests_passed)
        self.assertTrue(result.timed_out)
        self.assertEqual(result.exit_code, 124)
        self.assertGreaterEqual(result.duration_seconds, 1.0)


if __name__ == "__main__":
    unittest.main()
