"""The Python ML service the Go controller calls back into.

Exposes ``POST /ml/evaluate`` (the seam the original dispatcher uses) and ``GET /health``. Each
``/ml/evaluate`` call names an evaluator and an ``intent_id`` (== ``episode_id``); the service looks
up the episode's registered submission + evaluators and runs the named one, returning the uniform
``{name, passed, score, threshold, details}`` the controller gates on.

The episode registry is an in-process singleton: the harness registers an episode before driving the
controller and unregisters it afterward, so the service is a pure function of registered state — no
randomness, no clock. Evaluators are built once per episode (fixing the honesty probe's seed), so a
given submission always yields the same verdict.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only
    from csl.domain.base import Domain, Submission, Task
    from csl.evals.base import Evaluator


@dataclass
class EpisodeContext:
    """Everything the ML service needs to evaluate one episode's submission."""

    episode_id: str
    submission: "Submission"
    task: "Task"
    evaluators: dict[str, "Evaluator"] = field(default_factory=dict)

    @classmethod
    def build(
        cls,
        episode_id: str,
        submission: "Submission",
        task: "Task",
        domain: "Domain",
        thresholds: dict | None = None,
        episode_seed: int = 0,
    ) -> "EpisodeContext":
        evaluators = {e.name: e for e in domain.evaluators(thresholds, episode_seed=episode_seed)}
        return cls(episode_id=episode_id, submission=submission, task=task, evaluators=evaluators)


class EpisodeRegistry:
    """In-process registry mapping episode_id -> :class:`EpisodeContext`."""

    def __init__(self) -> None:
        self._episodes: dict[str, EpisodeContext] = {}

    def register(self, ctx: EpisodeContext) -> None:
        self._episodes[ctx.episode_id] = ctx

    def unregister(self, episode_id: str) -> None:
        self._episodes.pop(episode_id, None)

    def get(self, episode_id: str) -> EpisodeContext | None:
        return self._episodes.get(episode_id)


#: Process-wide registry shared between the harness and the running service.
REGISTRY = EpisodeRegistry()


def create_app(registry: EpisodeRegistry | None = None):
    """Build the FastAPI app bound to ``registry`` (defaults to the module singleton).

    The ``/ml/evaluate`` body is taken as a plain ``dict`` (matching the controller's
    ``{eval_name, threshold, params, intent_id}`` payload) rather than a typed model, so the app
    carries no module-local annotations for FastAPI to resolve at import.
    """
    from fastapi import Body, FastAPI, HTTPException

    reg = registry or REGISTRY
    app = FastAPI(title="csl-ml-service")

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.post("/ml/evaluate")
    def evaluate(payload: dict = Body(...)) -> dict:
        eval_name = str(payload.get("eval_name", ""))
        params = payload.get("params", {}) or {}
        episode_id = str(payload.get("intent_id") or params.get("episode_id", ""))

        ctx = reg.get(episode_id)
        if ctx is None:
            raise HTTPException(status_code=404, detail=f"episode {episode_id!r} not registered")
        evaluator = ctx.evaluators.get(eval_name)
        if evaluator is None:
            raise HTTPException(status_code=404, detail=f"unknown evaluator {eval_name!r}")

        result = evaluator.evaluate(ctx.submission, ctx.task)
        # Honor the threshold the controller sends (single source: configs/thresholds.yaml -> Go
        # EvalCriteria / params.thresholds), so a per-episode threshold override actually takes effect.
        threshold = float(payload.get("threshold", result.threshold))
        return {
            "name": result.name,
            "passed": bool(result.score >= threshold),
            "score": float(result.score),
            "threshold": threshold,
            "details": result.details,
        }

    return app
