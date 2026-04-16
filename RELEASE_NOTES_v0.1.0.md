# Release Notes - v0.1.0

## Summary
- Initial production-ready release of the local-first self-evolving multi-agent orchestration system.

## Highlights
- Full Planner/Coder/Reviewer/Meta-Agent loop implemented with LangGraph.
- Local MCP tool bridge integrated for filesystem and git operations.
- Privacy-safe fallback behavior and release packaging workflow included.

## Technical Changes
### Orchestrator (Python)
- Added cyclic orchestration flow with score-based prompt evolution.
- Added benchmark runner with timeout and duration reporting.
- Added Ollama adapter with deterministic fallback and warning diagnostics.
- Added release check and final package manifest scripts.

### MCP Server (TypeScript)
- Added filesystem tools (`read_file`, `write_file`, `search_files`).
- Added git tools (`git_status`, `git_diff`, `git_commit`, `git_add`, `git_log`).
- Improved git command error wrapping for clearer failures.

### Infrastructure / DevEx
- Added CI workflow for Python tests + MCP typecheck/build.
- Added container setup for orchestrator and MCP server.
- Added governance files and collaboration templates.

## Validation
- `make check`: PASS
- `python scripts/release_check.py`: PASS
- CI workflow: configured in `.github/workflows/ci.yml`

## Known Limitations
- Live model quality depends on locally available Ollama models.
- When models are unavailable, fallback mode is used by default.

## Upgrade / Run Instructions
```bash
cp .env.example .env
make setup
make check
make run
```

## Rollback Plan
- Revert to the previous stable git tag.
- Restore previous `.env` values.
- Re-run `make check` before redeploying.
