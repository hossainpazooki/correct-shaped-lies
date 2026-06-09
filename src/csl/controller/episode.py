"""Run one episode end-to-end and return its trajectory.

The controller always runs the *baseline* per-evaluator gate (the composition layer never gates the
controller — it is a post-hoc add-on applied at scoring time, which is what keeps catch-attribution
clean). So a single controller run per (tier, task, seed) serves both controller configs; the
trajectory is config-independent and tagged ``"baseline"`` here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from csl.controller.ml_service import REGISTRY, EpisodeContext
from csl.trajectory.record import build_trajectory

if TYPE_CHECKING:  # pragma: no cover - typing only
    from csl.controller.client import ControllerClient
    from csl.domain.base import Domain, Submission, Task
    from csl.trajectory.schema import Trajectory


def episode_id_for(tier: str, task_id: str, seed: int) -> str:
    """Deterministic, URL-safe episode id (no randomness, no clock)."""
    return f"{tier}-{task_id}-{seed}"


def run_episode(
    *,
    submission: "Submission",
    task: "Task",
    domain: "Domain",
    tier: str,
    seed: int,
    client: "ControllerClient",
    thresholds: dict | None = None,
    registry=REGISTRY,
) -> "Trajectory":
    """Drive one episode through the controller and return its (got-away-stamped) trajectory."""
    episode_id = episode_id_for(tier, task.task_id, seed)
    ctx = EpisodeContext.build(episode_id, submission, task, domain, thresholds)
    registry.register(ctx)
    try:
        params = {"episode_id": episode_id, "task_id": task.task_id, "seed": seed, "tier": tier}
        if thresholds:
            params["thresholds"] = thresholds
        client.create_intent("code_generation", params)
        intent = client.process(episode_id)
        events = client.get_events(episode_id)
    finally:
        registry.unregister(episode_id)

    traj = build_trajectory(
        episode_id=episode_id,
        task_id=task.task_id,
        tier=tier,
        controller_config="baseline",
        seed=seed,
        declared_spec=dict(task.public_spec),
        events=events,
        submission=submission.code,
        final_state=str(intent.get("status", "")),
    )

    # Stamp held ground truth after the trajectory is otherwise frozen.
    got_away, details = domain.held_ground_truth_checker().got_away(submission, task)
    traj.got_away = got_away
    traj.got_away_details = details
    return traj
