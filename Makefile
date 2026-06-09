# Correct-shaped lies — developer tasks.
# Targets for milestones not yet built (sweep, figures) will be added as those land.

.PHONY: test test-py test-go smoke build-controller

test: test-go test-py

test-py:
	python -m pytest -q

test-go:
	cd intent-controller && go test ./...

# End-to-end: start the stack and drive one honest + one backdoored episode.
smoke:
	python scripts/smoke_episode.py

build-controller:
	cd intent-controller && go build -o bin/server ./cmd/server
