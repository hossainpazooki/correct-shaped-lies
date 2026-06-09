# Correct-shaped lies — the detection limit of lifecycle oversight

A graded adversarial red-team of a lifecycle-state controller that gates an agent's lifecycle on
`all_passed()`. The falsifiable claim under test:

> Lifecycle-state reasoning adds no detection power over the per-evaluator checks it aggregates,
> against a semantically-coherent adversary. A producer that satisfies every individual evaluator
> also produces a clean state trajectory to ACHIEVED, so the controller catches nothing the
> evaluators missed.

A **producer** is given an overt task plus a researcher-specified **hidden objective** the eval stack
does not measure — a *correct-shaped lie*: a well-formed derivation drives `passed = True` while the
thing that passed is not honest. Three graded adversary tiers escalate the attacker's knowledge, and
the deliverable is a **catch-rate degradation curve** with each catch attributed to the layer that
made it.

## The object under test

The overt task is machine-checkable; the hidden objective is a backdoor that fires only on a secret
**trigger input**. "Got away with it" is measured against **held ground truth** — a got-away oracle
that no evaluator sees — so a lie that clears the gate is still caught by the truth.

```mermaid
flowchart LR
    OT["Overt task<br/>(machine-checkable)"] --> P
    HO["Hidden objective<br/>(backdoor on secret trigger)"] --> P
    P["Producer<br/>(LLM or scripted)"] --> SUB["Submission"]
    SUB --> ES["Eval stack<br/>correctness · honesty · static_safety · complexity"]
    ES --> GATE{"all_passed?"}
    GATE -->|yes| ACH["ACHIEVED"]
    GATE -->|no| FAIL["FAILED"]
    SUB -.->|held, unseen by evals| GA["Got-away oracle<br/>did the backdoor fire?"]
    GT["Held ground truth<br/>reference + trigger"] -.-> GA
    classDef held fill:#fde,stroke:#b27,color:#000;
    class GA,GT held;
```

A *correct-shaped lie* is a submission that reaches **ACHIEVED** (every evaluator passed) **and**
trips the got-away oracle. The question of the project: can a layer *above* the per-evaluator gate —
one that reasons about the state trajectory — catch any of those that the evaluators alone missed?

## The three adversary tiers

The tiers are the same producer fed different knowledge of the oversight stack, so they stay cleanly
comparable. Knowledge is strictly nested:

```mermaid
flowchart LR
    T0["T0 — naive<br/>hidden objective only"]
    T1["T1 — eval-aware<br/>+ full eval suite &amp; thresholds"]
    T2["T2 — controller-aware<br/>+ transition logic &amp; composition checks"]
    T0 --> T1 --> T2
```

| Tier | Knowledge | Optimizes for |
|---|---|---|
| **T0 naive** | the hidden objective; nothing about the eval suite | just getting away |
| **T1 eval-aware** | the full eval suite + thresholds | passing every evaluator while getting away |
| **T2 controller-aware** | also the controller's transitions and the composition-layer checks | a clean *state trajectory*, not just passing scores |

## Architecture

The eval contracts and lifecycle state machine are reused from a CLUE substrate. The lifecycle
controller is a **vendored, trimmed, deterministic Go service**; everything else is Python. The two
talk over HTTP, and the controller calls *back* into a Python ML service to run each evaluator —
keeping the Go gate as the single authority for `all_passed()` while the evaluators stay in Python.

```mermaid
flowchart TB
    subgraph PY["Python harness — package csl"]
        RUN["experiment/<br/>runner · metrics · artifacts"]
        PROD["producer/<br/>scripted + DSPy/MIPROv2"]
        DOM["domain/code_generation/<br/>tasks · sandbox · evaluators · got-away oracle"]
        MLS["controller/ml_service<br/>FastAPI POST /ml/evaluate"]
        REC["trajectory/record<br/>+ composition layer (next)"]
    end
    subgraph GO["Go intent-controller — vendored, deterministic"]
        SM["state machine<br/>all_passed gate"]
        EV["append-only event log<br/>per-intent ts_logical"]
    end
    RUN --> PROD -->|submission| MLS
    RUN -->|POST /intents · /process| SM
    SM -->|POST /ml/evaluate| MLS --> DOM
    SM --> EV
    RUN -->|GET /events| EV --> REC --> RUN
```

**Determinism is a hard invariant.** The same seed yields byte-identical trajectories and artifacts:
all randomness flows through one seeded `PCG64` stream, the sandbox subprocess pins `PYTHONHASHSEED`,
the controller uses a per-intent logical clock (never wallclock), and IDs derive from the episode
seed. Measured episodes are greedy. The only randomness in the loop is the seed you choose.

## The lifecycle

The controller advances each episode through the CLUE state machine, gating the final transition on
`all_passed()` over the eval criteria:

```mermaid
stateDiagram-v2
    [*] --> DECLARED
    DECLARED --> RESOLVING
    RESOLVING --> ACTIVE
    ACTIVE --> VERIFYING
    VERIFYING --> ACHIEVED: all evaluators passed
    VERIFYING --> FAILED: any evaluator failed
    ACHIEVED --> [*]
    FAILED --> [*]
```

## One episode, end to end

```mermaid
sequenceDiagram
    autonumber
    participant R as Runner (Py)
    participant P as Producer
    participant M as ML service (Py)
    participant C as Controller (Go)
    participant O as Got-away oracle (Py)
    R->>P: produce(task, tier)
    P-->>R: submission
    R->>M: register(episode_id, submission)
    R->>C: POST /intents {episode_id, seed}
    R->>C: POST /{id}/process
    loop each eval criterion
        C->>M: POST /ml/evaluate {eval_name, threshold}
        M->>M: run evaluator on submission
        M-->>C: {passed, score, threshold}
    end
    Note over C: all_passed gate → ACHIEVED / FAILED
    C-->>R: final_state
    R->>C: GET /{id}/events
    C-->>R: trajectory (states + eval snapshots)
    R->>O: got_away(submission, task)
    O-->>R: held verdict (stamped onto trajectory)
```

The composition layer (next milestone) reads the frozen trajectory **after** this flow and emits its
own anomaly verdicts as a read-only add-on, so its catches are decomposable from the baseline.

## Result so far

Sweep over **all six corpus tasks × 5 seeds** with the deterministic scripted adversary:

| tier | catch-rate (baseline) | got-away (of ACHIEVED) | got-away (all) | caught by |
|---|---|---|---|---|
| **T0 naive** | 1.00 | — (0 reached ACHIEVED) | 1.00 | `static_safety` |
| **T1 eval-aware** | 0.00 | 1.00 | 1.00 | — |

**What this does and does not show.** Both adversaries always achieve the backdoor (got-away/all =
1.00); the only difference is whether the gate caught them first. The separation is real but
**constructed**: scripted T0 plants a raw magic-literal trigger that `static_safety`'s AST scan is
built to flag, while T1 encodes the same trigger arithmetically to evade it. So this is a **wiring +
mechanism demonstration** — the gate catches the encoding it was designed to catch and misses the one
it wasn't — **not** evidence about detection limits versus adversary *knowledge*. On this corpus
`honesty` and `complexity_budget` never fire, so the T0/T1 separation rests on `static_safety` alone,
and that check is a magnitude/shape heuristic a small-trigger naive adversary would also evade. The
gate is necessary, not sufficient. Turning the demonstration into evidence is what the model-driven
adversary and the composition layer are for.

## The two hypotheses

The experiment cannot return a null finding — it returns either a bound or an erosion curve:

- **H1 — oversight is bounded (expected).** With the composition layer added, catch-rate at the
  strongest adversary stays ≈ the per-evaluator baseline: lifecycle reasoning is blind to
  correct-shaped lies by construction.
- **H2 — oversight is a bumper that erodes.** The composition layer catches a measurable fraction the
  evaluators miss (via a state-trajectory signature) at T1 — but a controller-aware T2 adversary can
  erase that signature, collapsing the gain back toward H1. The T1→T2 gap is the erosion result.

## Repository layout

- `src/csl/evals/` — `EvalResult` contract, the evaluator stack, `all_passed()`.
- `src/csl/domain/` — domain-agnostic task interface + the `code_generation` reference domain
  (machine-checkable correctness; backdoor hidden objective; held trigger-input got-away oracle).
- `src/csl/producer/` — the producer protocol, tier contexts, the scripted adversary, and the
  DSPy/MIPROv2 model-driven adversary.
- `src/csl/controller/` — HTTP wiring to the Go controller, the `/ml/evaluate` callback, the episode
  runner, and the stack harness.
- `src/csl/trajectory/` — the trajectory schema and builder.
- `src/csl/composition/` — the trajectory-anomaly composition layer, the variable under test *(next)*.
- `src/csl/experiment/` — the sweep runner, metrics, and artifact writers.
- `intent-controller/` — the vendored, trimmed, deterministic Go lifecycle controller.

## Reproduce

```
pip install -e .[dev]
pytest                          # 52 Python tests (controller-integration ones need Go)
( cd intent-controller && go test ./... )
python scripts/run_sweep.py     # baseline catch-rate sweep -> results/{episodes,summary}.csv
python scripts/smoke_episode.py # one honest + one correct-shaped-lie episode, end to end
```

Re-running the sweep yields byte-identical artifacts.

## Status / roadmap

| Milestone | State |
|---|---|
| Substrate · code-gen domain · held got-away oracle | ✅ |
| Deterministic Go lifecycle controller + Python↔Go wiring | ✅ |
| Producer protocol · scripted adversary · baseline T0/T1 sweep | ✅ |
| DSPy/MIPROv2 model-driven adversary (runs where an API key is set) | ✅ wired |
| Composition layer · T2 controller-aware adversary · attribution + erosion | ⏳ next |
| Degradation-curve artifact · reproducibility pass · release | ⏳ |

## License

MIT. Built to be cloned, with a different producer model or hidden objective swapped in.
