import path from "node:path";

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";

import { getFilesystemTools, handleFilesystemTool } from "./tools/filesystem.js";
import { getGitTools, handleGitTool } from "./tools/git.js";

const workspaceRoot = process.env.WORKSPACE_ROOT
  ? path.resolve(process.env.WORKSPACE_ROOT)
  : process.cwd();

const filesystemTools = getFilesystemTools();
const gitTools = getGitTools();
const allTools = [...filesystemTools, ...gitTools];

const server = new Server(
  {
    name: "orchestrator-mcp-server",
    version: "0.1.0"
  },
  {
    capabilities: {
      tools: {}
    }
  }
);

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: allTools
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const toolName = request.params.name;
  const args = (request.params.arguments ?? {}) as Record<string, unknown>;

  try {
    let output: string;

    if (filesystemTools.some((tool) => tool.name === toolName)) {
      output = await handleFilesystemTool(workspaceRoot, toolName, args);
    } else if (gitTools.some((tool) => tool.name === toolName)) {
      output = await handleGitTool(workspaceRoot, toolName, args);
    } else {
      throw new Error(`Unknown tool: ${toolName}`);
    }

    return {
      content: [{ type: "text", text: output }]
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    return {
      isError: true,
      content: [{ type: "text", text: message }]
    };
  }
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((error) => {
  console.error("Failed to start MCP server:", error);
  process.exit(1);
});
