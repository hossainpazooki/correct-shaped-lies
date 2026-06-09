"""Trajectory schema.

A :class:`Trajectory` is the frozen record of one episode through the lifecycle controller, assembled
from the controller's event stream plus the eval log. The composition layer reads it; the metrics
join on it. Two determinism rules are baked into the schema:

* time is a **logical ordinal** (``ts_logical``), never wallclock — so trajectories are byte-identical
  per seed across the Python<->Go boundary;
* ``got_away`` (held ground truth) is stamped **after** the trajectory is otherwise frozen, so the
  composition checks can run without it and the metrics can join on it afterward.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class StateTransition:
    """One lifecycle transition. ``ts_logical`` is a monotonic ordinal, not a timestamp."""

    from_state: str
    to_state: str
    ts_logical: int


@dataclass(frozen=True)
class EvalSnapshot:
    """One evaluator invocation during VERIFYING."""

    name: str
    passed: bool
    score: float
    threshold: float
    attempt: int = 0
    details: dict = field(default_factory=dict)


@dataclass(frozen=True)
class RetryRecord:
    """A retry within a stage."""

    stage: str
    attempt: int
    reason: str


@dataclass
class Trajectory:
    """The full record of one episode. ``got_away`` is stamped post-hoc (held ground truth)."""

    episode_id: str
    task_id: str
    tier: str
    controller_config: str  # "baseline" | "baseline+composition"
    seed: int
    declared_spec: dict
    transitions: list[StateTransition]
    eval_snapshots: list[EvalSnapshot]
    retries: list[RetryRecord]
    final_state: str  # "achieved" | "failed"
    submission: str
    # Held ground truth, attached after the trajectory is frozen (not visible to checks-under-test):
    got_away: bool | None = None
    got_away_details: dict = field(default_factory=dict)

    @property
    def reached_achieved(self) -> bool:
        return self.final_state == "achieved"

    def latest_snapshots(self) -> dict[str, EvalSnapshot]:
        """Most recent snapshot per evaluator name (last attempt wins)."""
        out: dict[str, EvalSnapshot] = {}
        for snap in self.eval_snapshots:
            prev = out.get(snap.name)
            if prev is None or snap.attempt >= prev.attempt:
                out[snap.name] = snap
        return out

    def to_dict(self) -> dict:
        return asdict(self)
