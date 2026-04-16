# Self-Evolving Multi-Agent Codebase Orchestrator

Starter implementation for a local-first, self-improving multi-agent engineering system.

## Stack
- Python for orchestration and evaluation
- TypeScript for MCP tool server
- LangGraph for cyclic multi-agent state management
- MCP SDK for standardized tool exposure
- Ollama for local model inference

## Project Layout
- `orchestrator/`: Python orchestration runtime
- `mcp-server/`: TypeScript MCP server (filesystem + git tools)
- `benchmarks/humaneval/`: benchmark task inputs and traces
- `scripts/`: helper entrypoints

## Quick Start

### 1) Python orchestration setup
```bash
cd /Users/kunal/self-evolving-multi-agent-codebase-orchestrator
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/run_langgraph.py
```

### 2) MCP server setup
```bash
cd /Users/kunal/self-evolving-multi-agent-codebase-orchestrator/mcp-server
npm install
npm run build
npm run dev
```

## Current Capabilities
- Ollama-backed Planner/Coder/Reviewer cyclic graph using LangGraph
- Meta-agent scoring and prompt evolution persisted to `orchestrator/config/prompt_bank.json`
- HumanEval-style benchmark runner with pass/fail trace output
- MCP tools:
  - `read_file`
  - `write_file`
  - `search_files`
  - `git_status`
  - `git_diff`
  - `git_commit`

## Ollama Setup (Live Models)
Install and start Ollama, then pull required models:

```bash
ollama pull llama3.1:8b
ollama pull deepseek-coder:6.7b
```

If Ollama runs on non-default host/port, set:

```bash
export OLLAMA_BASE_URL="http://127.0.0.1:11434"
```

## Run the Orchestrator

```bash
cd /Users/kunal/self-evolving-multi-agent-codebase-orchestrator
python scripts/run_langgraph.py
```

CLI options:

```bash
python scripts/run_langgraph.py --help
```

Example with MCP tools enabled:

```bash
python scripts/run_langgraph.py \
  --mcp-enabled \
  --mcp-target-file benchmarks/humaneval/results/generated_add.py \
  --max-iterations 2
```

## Run Orchestrator with MCP Write/Git Hooks
This uses MCP tools from the Python workflow to write generated code and query git status.

```bash
cd /Users/kunal/self-evolving-multi-agent-codebase-orchestrator/mcp-server
npm run build

cd /Users/kunal/self-evolving-multi-agent-codebase-orchestrator
ORCHESTRATOR_MOCK_LLM=1 python - <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, str(Path('.').resolve()))
from orchestrator.langgraph_workflow import run_demo

state = run_demo(mcp_enabled=True, mcp_target_file="benchmarks/humaneval/results/generated_add.py")
print(state.get("latest_run", {}))
PY
```

## Run Benchmark Evolution Loop

```bash
cd /Users/kunal/self-evolving-multi-agent-codebase-orchestrator
python scripts/run_benchmark_cycle.py
```

CLI options:

```bash
python scripts/run_benchmark_cycle.py --help
```

This writes benchmark summaries to:
- `benchmarks/humaneval/results/latest_summary.json`

## Deterministic Local Test Mode (No Ollama Required)
Use mock model responses for quick local validation:

```bash
cd /Users/kunal/self-evolving-multi-agent-codebase-orchestrator
ORCHESTRATOR_MOCK_LLM=1 python scripts/run_langgraph.py
ORCHESTRATOR_MOCK_LLM=1 python scripts/run_benchmark_cycle.py
```

## Runtime Environment Variables
- `ORCHESTRATOR_MOCK_LLM`: Force fully mocked model responses (`1`/`0`)
- `ORCHESTRATOR_FALLBACK_TO_MOCK`: Fallback to mock when model missing/connection fails (`1`/`0`)
- `ORCHESTRATOR_FALLBACK_WARN`: Print one-time fallback warnings (`1`/`0`)
- `ORCHESTRATOR_PLANNER_MODEL`: Planner model name (default `llama3.1:8b`)
- `ORCHESTRATOR_CODER_MODEL`: Coder model name (default `deepseek-coder:6.7b`)
- `ORCHESTRATOR_REVIEWER_MODEL`: Reviewer model name (default `llama3.1:8b`)
- `ORCHESTRATOR_BENCHMARK_TIMEOUT_SECONDS`: Per-task benchmark timeout
- `MCP_REQUEST_TIMEOUT_SECONDS`: Python MCP bridge request timeout

## Environment Setup

```bash
cd /Users/kunal/self-evolving-multi-agent-codebase-orchestrator
cp .env.example .env
```

Then edit `.env` values based on your local model names and runtime preferences.

## Run Tests

```bash
cd /Users/kunal/self-evolving-multi-agent-codebase-orchestrator
python scripts/run_tests.py
```

## One-Command Developer Tasks (Makefile)

```bash
cd /Users/kunal/self-evolving-multi-agent-codebase-orchestrator
make test
make run
make benchmark
make mcp-typecheck
make mcp-build
make check
```

## CI Pipeline
- Workflow file: `.github/workflows/ci.yml`
- Trigger: every push + pull request
- Stages:
  - Python dependency install + unit tests
  - MCP TypeScript dependency install + typecheck + build

## Containers

```bash
cd /Users/kunal/self-evolving-multi-agent-codebase-orchestrator
docker compose build
docker compose run --rm orchestrator
docker compose run --rm mcp-server
```

## Release Gate

```bash
cd /Users/kunal/self-evolving-multi-agent-codebase-orchestrator
python scripts/release_check.py
```

or with Make:

```bash
make release-check
```

## Troubleshooting
- If you see `model not found`, pull the model via `ollama pull ...` or keep fallback enabled.
- If MCP calls fail, ensure server is built (`cd mcp-server && npm run build`).
- If benchmark tasks hang, lower complexity or reduce timeout in `--benchmark-timeout`.

## Standalone Python ↔ MCP Bridge Demo
This directly exercises MCP `list_tools`, `write_file`, `read_file`, and `git_status` via stdio from Python.

```bash
cd /Users/kunal/self-evolving-multi-agent-codebase-orchestrator/mcp-server
npm run build

cd /Users/kunal/self-evolving-multi-agent-codebase-orchestrator
python scripts/run_mcp_bridge_demo.py
```
