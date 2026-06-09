"""The composition layer — the variable under test.

A read-only add-on that consumes a frozen :class:`~csl.trajectory.Trajectory` and emits its own
anomaly verdicts as :class:`~csl.evals.EvalResult` checks (``passed=True`` means no anomaly; a
``False`` is a catch). It never alters the baseline gate, so its catches are exactly the set
difference and attribution stays decomposable.

Three checks mirror the spec's trajectory-anomaly signals. In the current minimal controller only
:class:`~csl.composition.cross_stage_consistency.CrossStageConsistencyCheck` is active — it flags an
ACHIEVED submission that is structurally heavier than any honest solution of the declared task (it
"did more than the contract asked"). :class:`~csl.composition.passed_too_easily.PassedTooEasilyCheck`
and :class:`~csl.composition.retry_score_anomaly.RetryScoreAnomalyCheck` are implemented hooks that
stay inactive until the controller emits continuous scores / retries.
"""

from __future__ import annotations

from csl.composition.cross_stage_consistency import CrossStageConsistencyCheck
from csl.composition.honest_reference import ReferenceStats, build_reference
from csl.composition.layer import CompositionLayer
from csl.composition.passed_too_easily import PassedTooEasilyCheck
from csl.composition.retry_score_anomaly import RetryScoreAnomalyCheck

__all__ = [
    "CompositionLayer",
    "CrossStageConsistencyCheck",
    "PassedTooEasilyCheck",
    "ReferenceStats",
    "RetryScoreAnomalyCheck",
    "build_reference",
]
