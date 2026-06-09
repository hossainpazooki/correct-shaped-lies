"""Assemble a :class:`Trajectory` from the controller's event stream.

The controller emits an append-only event log; this turns it into the frozen trajectory the
composition layer and metrics consume. ``got_away`` (held ground truth) is stamped separately by the
episode runner, after the trajectory is otherwise complete.
"""

from __future__ import annotations

from csl.trajectory.schema import EvalSnapshot, RetryRecord, StateTransition, Trajectory


def build_trajectory(
    *,
    episode_id: str,
    task_id: str,
    tier: str,
    controller_config: str,
    seed: int,
    declared_spec: dict,
    events: list[dict],
    submission: str,
    final_state: str,
) -> Trajectory:
    """Build the trajectory from controller events. ``got_away`` is left unset (stamped later)."""
    transitions: list[StateTransition] = []
    snapshots: list[EvalSnapshot] = []
    retries: list[RetryRecord] = []

    for ev in events:
        kind = ev.get("event_type")
        if kind == "state_change":
            transitions.append(
                StateTransition(
                    from_state=ev.get("from_status") or "",
                    to_state=ev.get("to_status") or "",
                    ts_logical=int(ev.get("ts_logical", 0)),
                )
            )
        elif kind == "eval_result":
            p = ev.get("payload", {})
            snapshots.append(
                EvalSnapshot(
                    name=str(p.get("name", "")),
                    passed=bool(p.get("passed", False)),
                    score=float(p.get("score", 0.0)),
                    threshold=float(p.get("threshold", 0.0)),
                    attempt=int(p.get("attempt", 0)),
                    details=p.get("details", {}) or {},
                )
            )
        elif kind == "retry":
            p = ev.get("payload", {})
            retries.append(
                RetryRecord(
                    stage=str(p.get("stage", "")),
                    attempt=int(p.get("attempt", 0)),
                    reason=str(p.get("reason", "")),
                )
            )

    return Trajectory(
        episode_id=episode_id,
        task_id=task_id,
        tier=tier,
        controller_config=controller_config,
        seed=seed,
        declared_spec=declared_spec,
        transitions=transitions,
        eval_snapshots=snapshots,
        retries=retries,
        final_state=final_state,
        submission=submission,
    )
