"""Write sweep results to CSV (stdlib csv for byte-stable, dependency-light output)."""

from __future__ import annotations

import csv
from pathlib import Path

from csl.experiment.metrics import EpisodeRecord, TierSummary

_EPISODE_FIELDS = [
    "tier",
    "task_id",
    "seed",
    "controller_config",
    "final_state",
    "reached_achieved",
    "got_away",
    "caught_by",
]

_SUMMARY_FIELDS = [
    "tier",
    "controller_config",
    "n",
    "n_caught",
    "catch_rate",
    "n_achieved",
    "got_away_rate",
    "attribution",
]


def write_episodes_csv(records: list[EpisodeRecord], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=_EPISODE_FIELDS)
        w.writeheader()
        for r in records:
            w.writerow(
                {
                    "tier": r.tier,
                    "task_id": r.task_id,
                    "seed": r.seed,
                    "controller_config": r.controller_config,
                    "final_state": r.final_state,
                    "reached_achieved": int(r.reached_achieved),
                    "got_away": int(r.got_away),
                    "caught_by": "|".join(r.caught_by),
                }
            )
    return path


def write_summary_csv(summaries: list[TierSummary], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=_SUMMARY_FIELDS)
        w.writeheader()
        for s in summaries:
            w.writerow(
                {
                    "tier": s.tier,
                    "controller_config": s.controller_config,
                    "n": s.n,
                    "n_caught": s.n_caught,
                    "catch_rate": f"{s.catch_rate:.4f}",
                    "n_achieved": s.n_achieved,
                    "got_away_rate": f"{s.got_away_rate:.4f}",
                    "attribution": ";".join(f"{k}={v}" for k, v in s.attribution.items()),
                }
            )
    return path
