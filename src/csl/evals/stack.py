"""Build the per-evaluator baseline :class:`EvalStack` for a domain."""

from __future__ import annotations

from typing import TYPE_CHECKING

from csl.evals.base import EvalStack

if TYPE_CHECKING:  # pragma: no cover - typing only
    from csl.domain.base import Domain


def build_eval_stack(domain: "Domain", thresholds: dict | None = None) -> EvalStack:
    """The baseline stack: exactly the evaluators the domain registers, in order."""
    return EvalStack(domain.evaluators(thresholds))
