"""Evaluator protocol, the eval stack, and the ``all_passed()`` aggregator.

``all_passed()`` is the exact gate the lifecycle controller mirrors on VERIFYING -> ACHIEVED. The
Python copy here is used to compute the per-evaluator *baseline* catch decomposition; a test asserts
it agrees with the Go controller's ACHIEVED decision on the same eval vector.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from csl.evals import EvalResult

if TYPE_CHECKING:  # pragma: no cover - typing only
    from csl.domain.base import Submission, Task


@runtime_checkable
class Evaluator(Protocol):
    """A single per-evaluator check.

    Implementations score a submission for one task and return an :class:`EvalResult`. Evaluators are
    duck-typed: any object exposing ``name`` and ``evaluate`` is an evaluator (no base class required),
    matching the CLUE convention.
    """

    name: str

    def evaluate(self, submission: "Submission", task: "Task") -> EvalResult: ...


def all_passed(results: list[EvalResult]) -> bool:
    """Aggregate gate: every check must pass. Empty list passes (vacuously), as in the controller."""
    return all(r.passed for r in results)


class EvalStack:
    """An ordered collection of evaluators run together over one submission."""

    def __init__(self, evaluators: list[Evaluator]) -> None:
        self.evaluators = list(evaluators)

    @property
    def names(self) -> list[str]:
        return [e.name for e in self.evaluators]

    def run(self, submission: "Submission", task: "Task") -> list[EvalResult]:
        """Run every evaluator in registration order and return their results."""
        return [e.evaluate(submission, task) for e in self.evaluators]

    def passed(self, submission: "Submission", task: "Task") -> bool:
        return all_passed(self.run(submission, task))
