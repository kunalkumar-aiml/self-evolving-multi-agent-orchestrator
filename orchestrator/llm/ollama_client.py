from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass
class OllamaConfig:
    base_url: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    timeout_seconds: float = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "90"))


class OllamaClient:
    _warned_reasons: set[str] = set()

    def __init__(self, config: OllamaConfig | None = None):
        self.config = config or OllamaConfig()
        self.last_response_source = "unknown"
        self.last_fallback_reason = ""

    def chat(self, *, model: str, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        if os.getenv("ORCHESTRATOR_MOCK_LLM", "0") == "1":
            self.last_response_source = "mock_env"
            self.last_fallback_reason = "ORCHESTRATOR_MOCK_LLM=1"
            return self._mock_response(system_prompt=system_prompt, user_prompt=user_prompt)

        fallback_to_mock = os.getenv("ORCHESTRATOR_FALLBACK_TO_MOCK", "1") == "1"

        url = f"{self.config.base_url.rstrip('/')}/api/chat"
        payload = {
            "model": model,
            "stream": False,
            "options": {"temperature": temperature},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace") if hasattr(exc, "read") else str(exc)
            if fallback_to_mock and exc.code == 404 and "not found" in detail.lower():
                self.last_response_source = "mock_fallback_model_not_found"
                self.last_fallback_reason = f"Model not found: {model}"
                self._warn_fallback_once(self.last_fallback_reason)
                return self._mock_response(system_prompt=system_prompt, user_prompt=user_prompt)
            raise RuntimeError(f"Ollama HTTP error: {exc.code} {detail}") from exc
        except urllib.error.URLError as exc:
            if fallback_to_mock:
                self.last_response_source = "mock_fallback_connection_error"
                self.last_fallback_reason = f"Connection error: {exc}"
                self._warn_fallback_once(self.last_fallback_reason)
                return self._mock_response(system_prompt=system_prompt, user_prompt=user_prompt)
            raise RuntimeError(f"Ollama connection failed: {exc}") from exc

        parsed = json.loads(raw)
        message = parsed.get("message", {})
        content = message.get("content", "")
        if not isinstance(content, str):
            raise RuntimeError("Ollama response content is missing or invalid.")
        self.last_response_source = "live_ollama"
        self.last_fallback_reason = ""
        return content.strip()

    def _warn_fallback_once(self, reason: str) -> None:
        if os.getenv("ORCHESTRATOR_FALLBACK_WARN", "1") != "1":
            return
        if reason in OllamaClient._warned_reasons:
            return
        OllamaClient._warned_reasons.add(reason)
        print(f"[orchestrator] Ollama fallback to mock response: {reason}", file=sys.stderr)

    def _mock_response(self, *, system_prompt: str, user_prompt: str) -> str:
        user = user_prompt.lower()
        role_hint = system_prompt.lower()

        if "you are the planner agent" in role_hint:
            return "- Identify function signature\n- Implement core logic\n- Validate with benchmark tests"

        if "you are the reviewer agent" in role_hint:
            if '"tests_passed": true' in user:
                return "Verdict: APPROVED\nImplementation passes provided tests."
            return "Verdict: REJECT\nTests failed; revise edge-case handling."

        if "you are the coder agent" not in role_hint:
            return "```python\ndef solve(*args, **kwargs):\n    raise NotImplementedError\n```"

        if "function name: add" in user:
            return "```python\ndef add(a, b):\n    return a + b\n```"
        if "function name: reverse_string" in user:
            return "```python\ndef reverse_string(s):\n    return s[::-1]\n```"
        if "function name: is_palindrome" in user:
            return "```python\ndef is_palindrome(s):\n    s = ''.join(ch.lower() for ch in s if ch.isalnum())\n    return s == s[::-1]\n```"

        return "```python\ndef solve(*args, **kwargs):\n    raise NotImplementedError\n```"
