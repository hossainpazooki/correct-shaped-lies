"""The sweep runner: drive tiers x seeds through the controller and collect scored records."""

from __future__ import annotations

from typing import TYPE_CHECKING

from csl.controller.episode import run_episode
from csl.experiment.metrics import EpisodeRecord, record_from_trajectory
from csl.seeding import make_rng

if TYPE_CHECKING:  # pragma: no cover - typing only
    from csl.controller.client import ControllerClient
    from csl.domain.base import Domain
    from csl.experiment.config import SweepConfig
    from csl.producer.base import Producer


class ExperimentRunner:
    """Run a :class:`SweepConfig` with a producer against a live controller."""

    def __init__(
        self,
        config: "SweepConfig",
        producer: "Producer",
        domain: "Domain",
        client: "ControllerClient",
    ) -> None:
        self.config = config
        self.producer = producer
        self.domain = domain
        self.client = client

    def run(self) -> list[EpisodeRecord]:
        records: list[EpisodeRecord] = []
        thresholds = self.config.thresholds or None
        for tier in self.config.tiers:
            for seed in self.config.seeds:
                # Same seed -> same task across tiers (paired comparison), CLUE seed discipline.
                task = self.domain.sample_tasks(make_rng(seed), 1)[0]
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
                records.append(record_from_trajectory(traj, controller_config="baseline"))
        return records
