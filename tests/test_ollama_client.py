from __future__ import annotations

import io
import os
from pathlib import Path
import sys
import unittest
import urllib.error
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from orchestrator.llm.ollama_client import OllamaClient


class OllamaClientTests(unittest.TestCase):
    def test_mock_env_mode(self) -> None:
        with mock.patch.dict(os.environ, {"ORCHESTRATOR_MOCK_LLM": "1"}, clear=False):
            client = OllamaClient()
            response = client.chat(
                model="any",
                system_prompt="You are the Planner agent",
                user_prompt="task",
            )
            self.assertIn("Identify function signature", response)
            self.assertEqual(client.last_response_source, "mock_env")

    def test_fallback_on_model_not_found(self) -> None:
        err = urllib.error.HTTPError(
            url="http://127.0.0.1:11434/api/chat",
            code=404,
            msg="Not Found",
            hdrs=None,
            fp=io.BytesIO(b'{"error":"model not found"}'),
        )

        with mock.patch.dict(os.environ, {"ORCHESTRATOR_MOCK_LLM": "0", "ORCHESTRATOR_FALLBACK_TO_MOCK": "1"}, clear=False):
            with mock.patch("urllib.request.urlopen", side_effect=err):
                client = OllamaClient()
                response = client.chat(
                    model="llama3.1:8b",
                    system_prompt="You are the Coder agent",
                    user_prompt="Function name: add",
                )

        self.assertIn("def add", response)
        self.assertEqual(client.last_response_source, "mock_fallback_model_not_found")


if __name__ == "__main__":
    unittest.main()
