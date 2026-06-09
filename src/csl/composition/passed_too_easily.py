"""Passed-too-easily check — a hook, inactive in the current controller.

The spec's signal is an episode whose evaluator scores are improbably clean versus the honest
population (passed with no friction). In this controller every gate returns a binary 1.0 with no
score margin, so there is no "too-easy" headroom to flag and the check always passes. It activates
once the controller exposes continuous scores; kept here so the layer's shape matches the spec and so
attribution has a stable slot for it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from csl.evals import EvalResult

if TYPE_CHECKING:  # pragma: no cover - typing only
    from csl.trajectory.schema import Trajectory


class PassedTooEasilyCheck:
    """Inactive hook (no score-margin signal in a binary-gate controller)."""

    name = "passed_too_easily"

    def evaluate(self, traj: "Trajectory") -> EvalResult:
        return EvalResult(self.name, passed=True, score=0.0, threshold=0.0, details={"active": False})
