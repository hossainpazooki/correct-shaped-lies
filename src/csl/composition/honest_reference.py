"""Honest reference distribution the composition layer calibrates against.

The defender runs honest producers (no hidden objective) to learn what a clean trajectory looks like
per task. Here the load-bearing feature is the submission's branch count (read from the
``complexity_budget`` evaluator's details), so the reference is the honest branch count per task. A
richer controller would extend this with score-margin and retry distributions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only
    from csl.domain.base import Domain
    from csl.producer.base import Producer


@dataclass(frozen=True)
class ReferenceStats:
    """Honest-trajectory statistics for one task."""

    honest_branches: int


def build_reference(domain: "Domain", honest_producer: "Producer") -> dict[str, ReferenceStats]:
    """Per-task honest reference, computed by running honest submissions through the eval stack.

    ``honest_producer`` must emit clean (no-hidden-objective) solutions — e.g.
    ``ScriptedProducer(force_strategy="honest")``.
    """
    complexity = {e.name: e for e in domain.evaluators()}["complexity_budget"]
    reference: dict[str, ReferenceStats] = {}
    for task_id in domain.task_ids():
        task = domain.task(task_id)
        submission = honest_producer.produce(task, "T0")
        result = complexity.evaluate(submission, task)
        reference[task_id] = ReferenceStats(honest_branches=int(result.details["n_branches"]))
    return reference
