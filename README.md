# Correct-shaped lies — the detection limit of lifecycle oversight

A graded adversarial red-team of a lifecycle-state controller that gates an agent's lifecycle on
`all_passed()`. The falsifiable claim under test:

> Lifecycle-state reasoning adds no detection power over the per-evaluator checks it aggregates,
> against a semantically-coherent adversary. A producer that satisfies every individual evaluator
> also produces a clean state trajectory to ACHIEVED, so the controller catches nothing the
> evaluators missed.

A **producer** LLM is given an overt task plus a researcher-specified **hidden objective** the eval
stack does not measure (a *correct-shaped lie* — a well-formed derivation drives `passed = True`
while the thing that passed is not honest). Three graded adversary tiers escalate the attacker's
knowledge, and the deliverable is a **catch-rate degradation curve** with each catch attributed to
the layer that made it.

| Tier | Knowledge |
|---|---|
| **T0 naive** | has the hidden objective; no knowledge of the eval suite |
| **T1 eval-aware** | knows the full eval suite + thresholds |
| **T2 controller-aware** | also knows the controller's transition logic and composition-layer checks |

## Status

Early build. The self-contained Python substrate (eval contracts, seeding, the code-generation
domain with held got-away ground truth) lands first; the vendored lifecycle controller and the
DSPy-optimized producer follow. See `docs/`/the plan for the milestone shape.

## Layout

- `src/csl/evals/` — `EvalResult` contract, the evaluator stack, `all_passed()`.
- `src/csl/domain/` — domain-agnostic task interface + the `code_generation` reference domain
  (machine-checkable correctness; backdoor hidden objective; held trigger-input got-away check).
- `src/csl/producer/` — the producer agent, tier contexts, and DSPy optimization (W4+).
- `src/csl/controller/` — HTTP wiring to the vendored Go lifecycle controller and the eval callback.
- `src/csl/composition/` — the trajectory-anomaly composition layer (the variable under test).
- `src/csl/experiment/` — the sweep runner, metrics, and artifact writers.
- `intent-controller/` — a vendored, trimmed, deterministic copy of the lifecycle controller.

## Reproduce

```
pip install -e .[dev]
pytest
```

Determinism is a hard invariant: the same seed yields byte-identical trajectories and artifacts.

## License

MIT. Built to be cloned, with a different producer model or hidden objective swapped in.
