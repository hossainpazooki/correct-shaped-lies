# Correct-shaped lies — developer tasks.
# The figures target lands with the degradation-curve milestone.

.PHONY: test test-py test-go smoke sweep build-controller

test: test-go test-py

test-py:
	python -m pytest -q

test-go:
	cd intent-controller && go test ./...

# End-to-end: start the stack and drive one honest + one backdoored episode.
smoke:
	python scripts/smoke_episode.py

# Baseline catch-rate sweep -> results/{episodes,summary}.csv
sweep:
	python scripts/run_sweep.py

build-controller:
	cd intent-controller && go build -o bin/server ./cmd/server
