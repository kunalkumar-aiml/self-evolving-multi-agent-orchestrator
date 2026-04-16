# Self-Evolving Multi-Agent Orchestrator

[![CI](https://github.com/kunalkumar-aiml/self-evolving-multi-agent-orchestrator/actions/workflows/ci.yml/badge.svg)](https://github.com/kunalkumar-aiml/self-evolving-multi-agent-orchestrator/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

A local-first, self-improving multi-agent engineering runtime that plans, writes, reviews, evaluates, and iteratively improves its own prompts.

## Why I Built This
I wanted a practical sandbox to experiment with autonomous engineering loops without depending on hosted APIs.
The project is intentionally local-first, transparent, and easy to inspect so behavior stays debuggable while agents evolve over repeated benchmark runs.

## Features
- LangGraph cyclic flow: `Planner -> Coder -> Reviewer -> Meta-Agent`
- Ollama-first inference with deterministic fallback mode
- HumanEval-style benchmark execution with timeout-safe results
- TypeScript MCP server exposing filesystem and Git tooling
- Python MCP stdio bridge for tool execution from the orchestration loop
- CI, release checks, and final packaging manifest

## Repository Structure
- `orchestrator/`: Python orchestration, LLM adapters, evaluation, MCP bridge
- `mcp-server/`: TypeScript MCP server and tools
- `benchmarks/humaneval/`: benchmark tasks and summaries
- `scripts/`: runnable entrypoints, checks, and packaging utilities
- `tests/`: unit tests

## Quick Start

### 1) Setup Python
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Setup MCP Server
```bash
cd mcp-server
npm install
npm run build
cd ..
```

### 3) Run Orchestrator
```bash
python scripts/run_langgraph.py --max-iterations 2
```

### 4) Run Benchmark Cycle
```bash
python scripts/run_benchmark_cycle.py --max-iterations 2 --benchmark-timeout 8
```

## Configuration
Create local runtime config:

```bash
cp .env.example .env
```

Key variables:
- `ORCHESTRATOR_PLANNER_MODEL`
- `ORCHESTRATOR_CODER_MODEL`
- `ORCHESTRATOR_REVIEWER_MODEL`
- `ORCHESTRATOR_BENCHMARK_TIMEOUT_SECONDS`
- `ORCHESTRATOR_MOCK_LLM`
- `ORCHESTRATOR_FALLBACK_TO_MOCK`
- `ORCHESTRATOR_FALLBACK_WARN`
- `OLLAMA_BASE_URL`
- `MCP_REQUEST_TIMEOUT_SECONDS`

## Run Modes
- **Live mode:** Pull Ollama models and keep `ORCHESTRATOR_MOCK_LLM=0`
- **Deterministic local mode:** set `ORCHESTRATOR_MOCK_LLM=1`

## Developer Commands
```bash
make test
make run
make benchmark
make mcp-typecheck
make mcp-build
make check
make release-check
make final-pack
```

## Containers
```bash
docker compose build
docker compose run --rm orchestrator
docker compose run --rm mcp-server
```

## Release
- Run release gate: `python scripts/release_check.py`
- Build release manifest: `python scripts/final_pack.py`
- Follow `RELEASE_CHECKLIST.md` and `RELEASE_NOTES_TEMPLATE.md`

## Collaboration
- Contribution guide: `CONTRIBUTING.md`
- Code of conduct: `CODE_OF_CONDUCT.md`
- Security policy: `SECURITY.md`
- Changelog: `CHANGELOG.md`

## License
MIT — see `LICENSE`.
