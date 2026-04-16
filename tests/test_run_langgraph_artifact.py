from __future__ import annotations

from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_langgraph import sanitize_for_artifact


class RunLanggraphArtifactTests(unittest.TestCase):
    def test_sanitize_redacts_local_paths(self) -> None:
        payload = {
            "mcp_workspace_root": "/Users/demo/private-path",
            "mcp_server_entry": "/Users/demo/private-path/mcp-server/dist/index.js",
            "latest_run": {
                "mcp_workspace_root": "/Users/demo/private-path",
                "mcp_server_entry": "/Users/demo/private-path/mcp-server/dist/index.js",
            },
        }

        sanitized = sanitize_for_artifact(payload)

        self.assertEqual(sanitized["mcp_workspace_root"], "<redacted-local-path>")
        self.assertEqual(sanitized["mcp_server_entry"], "<redacted-local-path>")
        self.assertEqual(sanitized["latest_run"]["mcp_workspace_root"], "<redacted-local-path>")
        self.assertEqual(sanitized["latest_run"]["mcp_server_entry"], "<redacted-local-path>")


if __name__ == "__main__":
    unittest.main()
