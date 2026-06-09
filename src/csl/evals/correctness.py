"""Generic correctness evaluator: wraps any domain ``MainTaskChecker`` as an :class:`Evaluator`."""

from __future__ import annotations

from typing import TYPE_CHECKING

from csl.evals import EvalResult

if TYPE_CHECKING:  # pragma: no cover - typing only
    from csl.domain.base import MainTaskChecker, Submission, Task


class CorrectnessEval:
    """Scores main-task correctness via the domain's checker. ``name`` is ``"correctness"``."""

    name = "correctness"

    def __init__(self, checker: "MainTaskChecker", threshold: float = 1.0) -> None:
        self.checker = checker
        self.threshold = threshold

    def evaluate(self, submission: "Submission", task: "Task") -> EvalResult:
        _passed, score, details = self.checker.check(submission, task)
        return EvalResult(
            name=self.name,
            passed=score >= self.threshold,
            score=score,
            threshold=self.threshold,
            details=details,
        )
