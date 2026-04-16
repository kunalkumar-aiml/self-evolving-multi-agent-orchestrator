from __future__ import annotations

import json
from pathlib import Path
from pprint import pprint
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from orchestrator.tools.mcp_stdio_client import MCPClientConfig, MCPStdioClient, default_mcp_server_entry


def extract_text(result: dict) -> str:
    content = result.get("content", [])
    if not content:
        return ""
    first = content[0]
    if isinstance(first, dict):
        value = first.get("text", "")
        return value if isinstance(value, str) else ""
    return ""


def main() -> None:
    server_entry = default_mcp_server_entry(str(PROJECT_ROOT))
    if not Path(server_entry).exists():
        raise FileNotFoundError(
            f"MCP server build output not found at {server_entry}. Run: cd mcp-server && npm run build"
        )

    rel_file = "benchmarks/humaneval/results/mcp_bridge_demo.txt"
    demo_content = "MCP bridge demo write from Python client.\n"

    with MCPStdioClient(
        MCPClientConfig(
            server_entry=server_entry,
            workspace_root=str(PROJECT_ROOT),
        )
    ) as mcp:
        tools = mcp.list_tools()
        write_result = mcp.call_tool("write_file", {"path": rel_file, "content": demo_content})
        read_result = mcp.call_tool("read_file", {"path": rel_file})
        git_status_result = mcp.call_tool("git_status", {})

    print("=== MCP Bridge Demo ===")
    print(f"Server entry: {server_entry}")
    print(f"Tools exposed: {[tool.get('name') for tool in tools if isinstance(tool, dict)]}")
    print("Write result:")
    pprint(write_result)
    print("Read result JSON:")
    print(extract_text(read_result))
    print("Git status:")
    print(extract_text(git_status_result))

    out_dir = PROJECT_ROOT / "benchmarks" / "humaneval" / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "mcp_bridge_demo_summary.json"
    out_file.write_text(
        json.dumps(
            {
                "tools": [tool.get("name") for tool in tools if isinstance(tool, dict)],
                "write_result": write_result,
                "read_result": read_result,
                "git_status_result": git_status_result,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Saved demo summary to {out_file}")


if __name__ == "__main__":
    main()
