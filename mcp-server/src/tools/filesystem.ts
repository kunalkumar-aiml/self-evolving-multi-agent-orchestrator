import fs from "node:fs/promises";
import path from "node:path";

export type ToolDefinition = {
  name: string;
  description: string;
  inputSchema: Record<string, unknown>;
};

type SearchResult = {
  path: string;
  matchType: "filename" | "content";
};

const DEFAULT_MAX_RESULTS = 50;

function resolveSafePath(root: string, userPath: string): string {
  const absolute = path.resolve(root, userPath);
  const normalizedRoot = path.resolve(root);
  if (!absolute.startsWith(normalizedRoot)) {
    throw new Error("Path escapes allowed workspace root.");
  }
  return absolute;
}

async function walk(dir: string, files: string[] = []): Promise<string[]> {
  const entries = await fs.readdir(dir, { withFileTypes: true });

  for (const entry of entries) {
    if (entry.name === "node_modules" || entry.name === ".git" || entry.name === "dist") {
      continue;
    }
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      await walk(fullPath, files);
    } else {
      files.push(fullPath);
    }
  }

  return files;
}

export function getFilesystemTools(): ToolDefinition[] {
  return [
    {
      name: "read_file",
      description: "Read a UTF-8 file from the workspace.",
      inputSchema: {
        type: "object",
        properties: {
          path: { type: "string", description: "Relative file path from workspace root." }
        },
        required: ["path"]
      }
    },
    {
      name: "write_file",
      description: "Write UTF-8 content to a file in the workspace.",
      inputSchema: {
        type: "object",
        properties: {
          path: { type: "string", description: "Relative file path from workspace root." },
          content: { type: "string", description: "Content to write." }
        },
        required: ["path", "content"]
      }
    },
    {
      name: "search_files",
      description: "Search file names and text content in the workspace.",
      inputSchema: {
        type: "object",
        properties: {
          query: { type: "string", description: "Case-insensitive search query." },
          path: { type: "string", description: "Optional sub-directory root.", default: "." },
          max_results: { type: "number", description: "Maximum number of matches.", default: 50 }
        },
        required: ["query"]
      }
    }
  ];
}

export async function handleFilesystemTool(
  workspaceRoot: string,
  toolName: string,
  args: Record<string, unknown>
): Promise<string> {
  if (toolName === "read_file") {
    const userPath = String(args.path ?? "");
    const filePath = resolveSafePath(workspaceRoot, userPath);
    const content = await fs.readFile(filePath, "utf-8");
    return JSON.stringify({ path: userPath, content }, null, 2);
  }

  if (toolName === "write_file") {
    const userPath = String(args.path ?? "");
    const content = String(args.content ?? "");
    const filePath = resolveSafePath(workspaceRoot, userPath);
    await fs.mkdir(path.dirname(filePath), { recursive: true });
    await fs.writeFile(filePath, content, "utf-8");
    return JSON.stringify({ path: userPath, bytes_written: Buffer.byteLength(content) }, null, 2);
  }

  if (toolName === "search_files") {
    const query = String(args.query ?? "").toLowerCase().trim();
    const subPath = String(args.path ?? ".");
    const maxResults = Number(args.max_results ?? DEFAULT_MAX_RESULTS);

    if (!query) {
      throw new Error("search_files requires a non-empty query.");
    }

    const searchRoot = resolveSafePath(workspaceRoot, subPath);
    const allFiles = await walk(searchRoot);
    const results: SearchResult[] = [];

    for (const filePath of allFiles) {
      if (results.length >= maxResults) {
        break;
      }

      const relPath = path.relative(workspaceRoot, filePath);
      const fileNameMatch = path.basename(filePath).toLowerCase().includes(query);
      if (fileNameMatch) {
        results.push({ path: relPath, matchType: "filename" });
        continue;
      }

      try {
        const text = await fs.readFile(filePath, "utf-8");
        if (text.toLowerCase().includes(query)) {
          results.push({ path: relPath, matchType: "content" });
        }
      } catch {
      }
    }

    return JSON.stringify({ query, count: results.length, results }, null, 2);
  }

  throw new Error(`Unknown filesystem tool: ${toolName}`);
}
