"""Evaluation framework.

``EvalResult`` is the uniform shape every evaluator and every composition-layer check returns. It is
copied verbatim from the CLUE substrate (``upstream-label-correction/evals/__init__.py``) so the
contract is identical across the two projects — the whole point of reusing the platform.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EvalResult:
    """Result of a single evaluation check."""

    name: str
    passed: bool
    score: float
    threshold: float
    details: dict = field(default_factory=dict)
