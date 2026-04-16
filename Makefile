PYTHON ?= python3
ROOT ?= $(CURDIR)

.PHONY: setup test run benchmark mcp-build mcp-typecheck check release-check release-tag final-pack docker-build docker-run docker-run-mcp

setup:
	cd "$(ROOT)" && $(PYTHON) -m pip install -r requirements.txt

test:
	cd "$(ROOT)" && $(PYTHON) scripts/run_tests.py

run:
	cd "$(ROOT)" && $(PYTHON) scripts/run_langgraph.py --max-iterations 2

benchmark:
	cd "$(ROOT)" && $(PYTHON) scripts/run_benchmark_cycle.py --max-iterations 2 --benchmark-timeout 8

mcp-typecheck:
	cd "$(ROOT)/mcp-server" && npm run typecheck

mcp-build:
	cd "$(ROOT)/mcp-server" && npm run build

check: test mcp-typecheck mcp-build

release-check:
	cd "$(ROOT)" && $(PYTHON) scripts/release_check.py

release-tag:
	@if [ -z "$(VERSION)" ]; then echo "Usage: make release-tag VERSION=0.1.0"; exit 1; fi
	cd "$(ROOT)" && $(PYTHON) scripts/tag_release.py --version "$(VERSION)" --push

final-pack:
	cd "$(ROOT)" && $(PYTHON) scripts/final_pack.py

docker-build:
	cd "$(ROOT)" && docker compose build

docker-run:
	cd "$(ROOT)" && docker compose run --rm orchestrator

docker-run-mcp:
	cd "$(ROOT)" && docker compose run --rm mcp-server
