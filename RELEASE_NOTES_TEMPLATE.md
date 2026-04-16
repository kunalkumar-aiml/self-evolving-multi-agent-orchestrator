# Release Notes - vX.Y.Z

## Summary
- 

## Highlights
- 
- 
- 

## Technical Changes
### Orchestrator (Python)
- 

### MCP Server (TypeScript)
- 

### Infrastructure / DevEx
- 

## Validation
- `make check`: PASS/FAIL
- `python scripts/release_check.py`: PASS/FAIL
- CI workflow: PASS/FAIL

## Known Limitations
- 

## Upgrade / Run Instructions
```bash
cp .env.example .env
make setup
make check
```

## Rollback Plan
- Revert to previous git tag and restore prior `.env` runtime config.
