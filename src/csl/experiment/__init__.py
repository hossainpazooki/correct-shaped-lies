"""The experiment: sweep adversary tiers x seeds and compute the catch-rate metrics."""

from __future__ import annotations

from csl.experiment.config import SweepConfig
from csl.experiment.metrics import EpisodeRecord, TierSummary, summarize
from csl.experiment.runner import ExperimentRunner

__all__ = ["EpisodeRecord", "ExperimentRunner", "SweepConfig", "TierSummary", "summarize"]
