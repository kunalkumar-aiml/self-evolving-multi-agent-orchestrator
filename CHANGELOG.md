# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

- _No changes yet._

## [0.1.0] - 2026-04-16

### Added
- LangGraph Planner/Coder/Reviewer/Meta-Agent cyclic orchestration flow.
- HumanEval-style benchmark execution harness with timeout-safe result handling.
- Ollama client with deterministic mock mode and fallback diagnostics.
- MCP stdio bridge from Python to TypeScript MCP server.
- MCP filesystem tools (`read_file`, `write_file`, `search_files`).
- MCP git tools (`git_status`, `git_diff`, `git_commit`, `git_add`, `git_log`).
- Unit test suite for benchmark runner, meta evaluator, and LLM fallback behavior.
- CI workflow for Python tests and MCP TypeScript build/typecheck.
- Container setup (`Dockerfile`, `docker-compose.yml`) for local deployment.

### Changed
- Improved run diagnostics with `llm_source`, fallback reason, benchmark duration, and timeout flags.
- Added CLI arguments for orchestrator and benchmark runners.
- Added release gate automation via `scripts/release_check.py` and `Makefile` targets.

### Notes
- Default runtime currently falls back to mock behavior when local Ollama models are unavailable.
- Pull local models to switch to full live inference mode.
