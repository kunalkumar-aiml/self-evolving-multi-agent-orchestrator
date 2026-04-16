import { promisify } from "node:util";
import { execFile } from "node:child_process";

import type { ToolDefinition } from "./filesystem.js";

const execFileAsync = promisify(execFile);

async function runGit(cwd: string, args: string[]): Promise<string> {
  try {
    const { stdout, stderr } = await execFileAsync("git", args, { cwd });
    return [stdout, stderr].filter(Boolean).join("\n").trim();
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    throw new Error(`git ${args.join(" ")} failed: ${message}`);
  }
}

export function getGitTools(): ToolDefinition[] {
  return [
    {
      name: "git_status",
      description: "Get concise git status for the workspace.",
      inputSchema: {
        type: "object",
        properties: {}
      }
    },
    {
      name: "git_diff",
      description: "Get git diff output. Use --staged when requested.",
      inputSchema: {
        type: "object",
        properties: {
          staged: { type: "boolean", default: false },
          pathspec: { type: "string", description: "Optional pathspec." }
        }
      }
    },
    {
      name: "git_commit",
      description: "Create a git commit with a message.",
      inputSchema: {
        type: "object",
        properties: {
          message: { type: "string", description: "Commit message." }
        },
        required: ["message"]
      }
    },
    {
      name: "git_add",
      description: "Stage files before commit (supports specific pathspec or all).",
      inputSchema: {
        type: "object",
        properties: {
          pathspec: { type: "string", description: "Optional pathspec to stage." },
          all: { type: "boolean", default: false }
        }
      }
    },
    {
      name: "git_log",
      description: "Get recent commit log in one-line format.",
      inputSchema: {
        type: "object",
        properties: {
          limit: { type: "number", default: 10 }
        }
      }
    }
  ];
}

export async function handleGitTool(
  workspaceRoot: string,
  toolName: string,
  args: Record<string, unknown>
): Promise<string> {
  if (toolName === "git_status") {
    const out = await runGit(workspaceRoot, ["status", "--short", "--branch"]);
    return out || "No output from git status.";
  }

  if (toolName === "git_diff") {
    const staged = Boolean(args.staged ?? false);
    const pathspec = args.pathspec ? String(args.pathspec) : undefined;

    const gitArgs = ["diff"];
    if (staged) {
      gitArgs.push("--staged");
    }
    if (pathspec) {
      gitArgs.push("--", pathspec);
    }

    const out = await runGit(workspaceRoot, gitArgs);
    return out || "No diff.";
  }

  if (toolName === "git_commit") {
    const message = String(args.message ?? "").trim();
    if (!message) {
      throw new Error("git_commit requires a non-empty message.");
    }

    const out = await runGit(workspaceRoot, ["commit", "-m", message]);
    return out || "Commit completed.";
  }

  if (toolName === "git_add") {
    const all = Boolean(args.all ?? false);
    const pathspec = args.pathspec ? String(args.pathspec) : undefined;

    if (all) {
      const out = await runGit(workspaceRoot, ["add", "-A"]);
      return out || "Staged all changes.";
    }

    if (!pathspec) {
      throw new Error("git_add requires either all=true or a pathspec.");
    }

    const out = await runGit(workspaceRoot, ["add", "--", pathspec]);
    return out || `Staged pathspec: ${pathspec}`;
  }

  if (toolName === "git_log") {
    const limit = Number(args.limit ?? 10);
    const safeLimit = Number.isFinite(limit) ? Math.max(1, Math.min(100, Math.floor(limit))) : 10;
    const out = await runGit(workspaceRoot, ["log", `-${safeLimit}`, "--oneline", "--decorate"]);
    return out || "No commits found.";
  }

  throw new Error(`Unknown git tool: ${toolName}`);
}
