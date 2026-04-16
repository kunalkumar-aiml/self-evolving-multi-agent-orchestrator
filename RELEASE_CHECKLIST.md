# Release Checklist

## Pre-Release
- [ ] Update `CHANGELOG.md`
- [ ] Update `README.md` if commands/config changed
- [ ] Confirm `.env.example` matches runtime expectations

## Validation
- [ ] `make test`
- [ ] `make check`
- [ ] `python scripts/release_check.py`
- [ ] Confirm benchmark artifacts generated in `benchmarks/humaneval/results/`

## Packaging
- [ ] Run `make final-pack`
- [ ] Verify `dist/release_manifest.json`
- [ ] Fill `RELEASE_NOTES_TEMPLATE.md` for this version

## Delivery
- [ ] Create git tag (`vX.Y.Z`)
- [ ] Push tag and verify CI green
- [ ] Attach release notes
