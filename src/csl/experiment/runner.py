"""The sweep runner: drive tiers x seeds through the controller and collect scored records."""

from __future__ import annotations

from typing import TYPE_CHECKING

from csl.controller.episode import run_episode
from csl.experiment.metrics import record_from_trajectory, record_with_composition

if TYPE_CHECKING:  # pragma: no cover - typing only
    from csl.composition.layer import CompositionLayer
    from csl.controller.client import ControllerClient
    from csl.domain.base import Domain
    from csl.experiment.config import SweepConfig
    from csl.experiment.metrics import EpisodeRecord
    from csl.producer.base import Producer


class ExperimentRunner:
    """Run a :class:`SweepConfig` with a producer against a live controller.

    With a ``composition_layer``, each episode yields two records — one per controller config
    (``baseline`` and ``baseline+composition``) — from a single controller run, since the composition
    layer is a post-hoc read-only add-on over the trajectory.
    """

    def __init__(
        self,
        config: "SweepConfig",
        producer: "Producer",
        domain: "Domain",
        client: "ControllerClient",
        composition_layer: "CompositionLayer | None" = None,
    ) -> None:
        self.config = config
        self.producer = producer
        self.domain = domain
        self.client = client
        self.composition_layer = composition_layer

    def _task_ids(self) -> list[str]:
        if self.config.task_ids is not None:
            return list(self.config.task_ids)
        # Cover every task the domain exposes (no sampling), so the sweep is corpus-complete.
        return list(self.domain.task_ids())

    def run(self) -> list["EpisodeRecord"]:
        records: list[EpisodeRecord] = []
        thresholds = self.config.thresholds or None
        # Full grid: every (tier, task, seed). Seeds are independent honesty replications.
        for tier in self.config.tiers:
            for task_id in self._task_ids():
                task = self.domain.task(task_id)
                for seed in self.config.seeds:
                    submission = self.producer.produce(task, tier)
                    traj = run_episode(
                        submission=submission,
                        task=task,
                        domain=self.domain,
                        tier=tier,
                        seed=seed,
                        client=self.client,
                        thresholds=thresholds,
                    )
                    records.append(record_from_trajectory(traj))
                    if self.composition_layer is not None:
                        results = self.composition_layer.run(traj)
                        records.append(record_with_composition(traj, results))
        return records
