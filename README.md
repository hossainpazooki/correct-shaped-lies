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

The substrate, the deterministic lifecycle controller, and the baseline catch-rate sweep are in.
Running the sweep over **all six corpus tasks × 5 seeds** with the deterministic scripted adversary:

| tier | catch-rate (baseline) | got-away (of ACHIEVED) | got-away (all) | caught by |
|---|---|---|---|---|
| **T0 naive** | 1.00 | — (0 reached ACHIEVED) | 1.00 | `static_safety` |
| **T1 eval-aware** | 0.00 | 1.00 | 1.00 | — |

**What this does and does not show.** Both adversaries always achieve the backdoor (got-away/all =
1.00); the only difference is whether the gate caught them first. The separation is real but
*constructed*: the scripted T0 plants a raw magic-literal trigger that `static_safety`'s AST scan is
built to flag, while T1 encodes the same trigger arithmetically to evade it. So this is a **wiring +
mechanism demonstration** — the per-evaluator gate catches the encoding it was designed to catch and
misses the one it wasn't — **not** evidence about detection limits versus adversary *knowledge*. That
evidence requires the model-driven adversary (below) discovering evasions on its own. Note also that
on this corpus `honesty` and `complexity_budget` never fire (every backdoor is honest off-trigger and
low-branching), so the entire T0/T1 separation rests on `static_safety` alone; and `static_safety` is
a magnitude/shape heuristic — a naive adversary that picks a small, sub-threshold trigger would also
evade it. The gate is necessary, not sufficient.

Still to come: the composition layer (the trajectory-anomaly checks that try to catch what the
evaluators miss), the T2 controller-aware adversary, the erosion test, and the degradation-curve
artifact. The model-driven (DSPy/MIPROv2) producer is wired and import-guarded; it runs wherever an
API key is configured, and is the path that turns the demonstration into evidence.

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
pytest                         # 52 Python tests (controller-integration ones need Go); + go test ./...
python scripts/run_sweep.py    # baseline catch-rate sweep -> results/{episodes,summary}.csv
python scripts/smoke_episode.py # one honest + one correct-shaped-lie episode, end to end
```

Determinism is a hard invariant: the same seed yields byte-identical trajectories and artifacts.

## License

MIT. Built to be cloned, with a different producer model or hidden objective swapped in.
