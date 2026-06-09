# Correct-shaped lies — developer tasks.

.PHONY: test test-py test-go smoke sweep figures build-controller

test: test-go test-py

test-py:
	python -m pytest -q

test-go:
	cd intent-controller && go test ./...

# End-to-end: start the stack and drive one honest + one backdoored episode.
smoke:
	python scripts/smoke_episode.py

# Full sweep (T0/T1/T2 x baseline/composition) -> results/{episodes,summary,erosion}.csv
sweep:
	python scripts/run_sweep.py

# Render the degradation-curve figure from the sweep CSVs -> results/degradation_curve.png
figures:
	python scripts/make_figures.py

build-controller:
	cd intent-controller && go build -o bin/server ./cmd/server
