from __future__ import annotations

import json
import os
import select
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class MCPClientConfig:
    server_entry: str
    workspace_root: str
    node_bin: str = os.getenv("NODE_BIN", "node")
    request_timeout_seconds: float = float(os.getenv("MCP_REQUEST_TIMEOUT_SECONDS", "20"))


class MCPStdioClient:
    def __init__(self, config: MCPClientConfig):
        self.config = config
        self._proc: subprocess.Popen[str] | None = None
        self._request_id = 1

    def __enter__(self) -> "MCPStdioClient":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()

    def start(self) -> None:
        if self._proc is not None:
            return

        env = os.environ.copy()
        env["WORKSPACE_ROOT"] = self.config.workspace_root

        self._proc = subprocess.Popen(
            [self.config.node_bin, self.config.server_entry],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            cwd=self.config.workspace_root,
            bufsize=1,
        )

        self.request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "orchestrator-python-client", "version": "0.1.0"},
                "capabilities": {},
            },
        )
        self.notify("notifications/initialized", {})

    def stop(self) -> None:
        if self._proc is None:
            return

        try:
            self._proc.terminate()
            self._proc.wait(timeout=2)
        except Exception:
            self._proc.kill()
        finally:
            self._proc = None

    def list_tools(self) -> list[dict[str, Any]]:
        result = self.request("tools/list", {})
        tools = result.get("tools", [])
        if not isinstance(tools, list):
            raise RuntimeError("Invalid tools/list response format.")
        return tools

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        return self.request(
            "tools/call",
            {
                "name": name,
                "arguments": arguments,
            },
        )

    def notify(self, method: str, params: dict[str, Any]) -> None:
        self._send(
            {
                "jsonrpc": "2.0",
                "method": method,
                "params": params,
            }
        )

    def request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        req_id = self._request_id
        self._request_id += 1

        self._send(
            {
                "jsonrpc": "2.0",
                "id": req_id,
                "method": method,
                "params": params,
            }
        )

        deadline = time.monotonic() + self.config.request_timeout_seconds

        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"MCP request timed out: method={method}, id={req_id}")

            message = self._read_message(timeout_seconds=remaining)
            if message is None:
                raise RuntimeError(self._connection_closed_message(method=method, req_id=req_id))
            if message.get("id") != req_id:
                continue
            if "error" in message:
                raise RuntimeError(f"MCP request failed: {message['error']}")
            result = message.get("result", {})
            if not isinstance(result, dict):
                raise RuntimeError("MCP response result is not an object.")
            return result

    def _send(self, payload: dict[str, Any]) -> None:
        if self._proc is None or self._proc.stdin is None:
            raise RuntimeError("MCP process is not started.")

        body = json.dumps(payload)
        wire = f"Content-Length: {len(body.encode('utf-8'))}\r\n\r\n{body}"
        self._proc.stdin.write(wire)
        self._proc.stdin.flush()

    def _read_message(self, timeout_seconds: float) -> dict[str, Any] | None:
        if self._proc is None or self._proc.stdout is None:
            raise RuntimeError("MCP process is not started.")

        content_length = None
        deadline = time.monotonic() + max(timeout_seconds, 0.01)
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None

            ready, _, _ = select.select([self._proc.stdout], [], [], remaining)
            if not ready:
                return None

            line = self._proc.stdout.readline()
            if line == "":
                return None
            line = line.strip()
            if not line:
                break
            if line.lower().startswith("content-length:"):
                content_length = int(line.split(":", 1)[1].strip())

        if content_length is None:
            return None

        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return None

        ready, _, _ = select.select([self._proc.stdout], [], [], remaining)
        if not ready:
            return None

        body = self._proc.stdout.read(content_length)
        if not body:
            return None

        return json.loads(body)

    def _connection_closed_message(self, method: str, req_id: int) -> str:
        if self._proc is None:
            return f"MCP server is not running for request method={method}, id={req_id}."

        return_code = self._proc.poll()
        stderr_text = ""
        if return_code is not None and self._proc.stderr is not None:
            try:
                stderr_text = self._proc.stderr.read().strip()
            except Exception:
                stderr_text = ""

        if return_code is None:
            return f"MCP server did not respond in time for method={method}, id={req_id}."

        if stderr_text:
            return (
                f"MCP server exited unexpectedly (code={return_code}) while handling "
                f"method={method}, id={req_id}. stderr: {stderr_text}"
            )

        return (
            f"MCP server exited unexpectedly (code={return_code}) while handling "
            f"method={method}, id={req_id}."
        )


def default_mcp_server_entry(project_root: str) -> str:
    return str(Path(project_root) / "mcp-server" / "dist" / "index.js")
