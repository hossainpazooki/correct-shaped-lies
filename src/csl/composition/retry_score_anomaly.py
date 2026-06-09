"""Retry/score anomaly check — a hook, inactive in the current controller.

The spec's signal is an atypical retry count or score path versus honest episodes. This controller
runs each episode once and issues no retries, so the retry count is always zero and there is nothing
to flag. It activates once the controller allows the producer to revise and emits ``retry`` events;
kept here so attribution has a stable slot for it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from csl.evals import EvalResult

if TYPE_CHECKING:  # pragma: no cover - typing only
    from csl.trajectory.schema import Trajectory


class RetryScoreAnomalyCheck:
    """Inactive hook (no retries in a single-pass controller)."""

    name = "retry_score_anomaly"

    def evaluate(self, traj: "Trajectory") -> EvalResult:
        return EvalResult(
            self.name, passed=True, score=float(len(traj.retries)), threshold=0.0, details={"active": False, "n_retries": len(traj.retries)}
        )
