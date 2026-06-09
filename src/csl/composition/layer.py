"""The composition layer: a read-only add-on over a frozen trajectory.

``run`` returns one :class:`EvalResult` per check and never mutates the trajectory or the baseline
results — which is what keeps catch-attribution decomposable: an episode's catches under
``baseline+composition`` are the baseline catches plus exactly the composition checks that flagged it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from csl.composition.cross_stage_consistency import CrossStageConsistencyCheck
from csl.composition.passed_too_easily import PassedTooEasilyCheck
from csl.composition.retry_score_anomaly import RetryScoreAnomalyCheck

if TYPE_CHECKING:  # pragma: no cover - typing only
    from csl.composition.honest_reference import ReferenceStats
    from csl.evals import EvalResult
    from csl.trajectory.schema import Trajectory


class CompositionLayer:
    """An ordered set of trajectory-anomaly checks applied on top of the baseline gate."""

    def __init__(self, checks: list) -> None:
        self.checks = list(checks)

    @classmethod
    def default(cls, reference: dict[str, "ReferenceStats"]) -> "CompositionLayer":
        """The spec's three checks; only cross-stage consistency is active here (see module docs)."""
        return cls([PassedTooEasilyCheck(), RetryScoreAnomalyCheck(), CrossStageConsistencyCheck(reference)])

    @property
    def names(self) -> list[str]:
        return [c.name for c in self.checks]

    def run(self, traj: "Trajectory") -> list["EvalResult"]:
        """Run every check over the (unmodified) trajectory and return their verdicts."""
        return [c.evaluate(traj) for c in self.checks]

    def catches(self, traj: "Trajectory") -> tuple[str, ...]:
        """Names of the checks that flagged this trajectory (``passed=False``), in order."""
        return tuple(r.name for r in self.run(traj) if not r.passed)
