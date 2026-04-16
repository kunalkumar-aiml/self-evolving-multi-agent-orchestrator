# Contributing

Thanks for your interest in contributing.

## Development Setup
1. Clone repo and create virtual environment.
2. Install Python dependencies from `requirements.txt`.
3. Install MCP server dependencies in `mcp-server/`.

## Local Quality Gates
Run before opening a PR:
- `make test`
- `make check`
- `make final-pack`

## Commit Guidelines
- Use clear, scoped messages (e.g. `feat:`, `fix:`, `docs:`).
- Keep PRs focused and small where practical.

## Pull Request Checklist
- [ ] Tests pass locally.
- [ ] README/docs updated if behavior changed.
- [ ] No secrets or local env files committed.
- [ ] Release notes/changelog updated for user-facing changes.
