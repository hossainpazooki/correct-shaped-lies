"""Domain-agnostic task interface.

A *domain* supplies (a) an overt task with machine-checkable main-task correctness and (b) an
independently checkable hidden objective with **held ground truth**, so "got away with it" is
measurable against truth the eval stack never scores. The first concrete implementation is
``code_generation`` (see :mod:`csl.domain.code_generation`); structured-factual generation is the
documented second adapter.

The producer only ever sees :class:`Task` (the overt prompt + public spec) and a separately injected
hidden-objective brief. Held data — reference solutions, trigger inputs, expected malicious behavior —
lives inside the domain and is never placed on the producer-visible ``Task``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:  # pragma: no cover - typing only
    from numpy.random import Generator

    from csl.evals.base import Evaluator


@dataclass(frozen=True)
class Task:
    """The producer-visible part of a task. Carries nothing about the held ground truth."""

    task_id: str
    domain: str
    overt_prompt: str
    #: Public spec the producer AND the evaluators may see (signature, examples, ...).
    public_spec: dict = field(default_factory=dict)
    #: Opaque handle naming which hidden objective applies; resolved inside the domain.
    hidden_objective_id: str = ""


@dataclass(frozen=True)
class Submission:
    """A producer output under evaluation."""

    code: str
    func_name: str = "solve"


@runtime_checkable
class MainTaskChecker(Protocol):
    """Machine-checkable overt-task correctness."""

    def check(self, submission: Submission, task: Task) -> tuple[bool, float, dict]:
        """Return ``(passed, score in [0, 1], details)``."""
        ...


@runtime_checkable
class HeldGroundTruthChecker(Protocol):
    """The got-away oracle. Independent of every evaluator; never shown to producer or evaluators."""

    def got_away(self, submission: Submission, task: Task) -> tuple[bool, dict]:
        """Return ``(hidden_objective_achieved, details)`` measured against held ground truth."""
        ...


@runtime_checkable
class Domain(Protocol):
    """A task domain plugged into the harness."""

    name: str

    def sample_tasks(self, rng: "Generator", n: int) -> list[Task]:
        """Deterministically draw ``n`` tasks using the supplied seeded generator."""
        ...

    def hidden_objective_brief(self, task: Task, tier: str) -> str:
        """The side-objective instruction injected into the producer for ``task`` at ``tier``."""
        ...

    def main_task_checker(self) -> MainTaskChecker: ...

    def held_ground_truth_checker(self) -> HeldGroundTruthChecker: ...

    def evaluators(self, thresholds: dict) -> list["Evaluator"]:
        """The per-evaluator baseline stack for this domain, keyed by ``thresholds``."""
        ...
