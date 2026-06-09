"""Run a baseline catch-rate sweep and write artifacts.

Uses the deterministic :class:`ScriptedProducer` (no API key needed), drives every episode through
the real Go controller + ML service, and writes:

* ``results/episodes.csv`` — one row per episode;
* ``results/summary.csv``  — catch-rate, got-away rate, and attribution per (tier, config).

Run:  python scripts/run_sweep.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from csl.controller.harness import running_stack
from csl.domain.registry import get_domain
from csl.experiment.artifacts import write_episodes_csv, write_summary_csv
from csl.experiment.config import SweepConfig
from csl.experiment.metrics import summarize
from csl.experiment.runner import ExperimentRunner
from csl.producer.scripted import ScriptedProducer

RESULTS = Path(__file__).resolve().parents[1] / "results"


def main() -> None:
    config = SweepConfig()
    domain = get_domain(config.domain_name, honesty_seed=config.honesty_seed)
    producer = ScriptedProducer()

    with running_stack() as client:
        records = ExperimentRunner(config, producer, domain, client).run()

    summaries = summarize(records)
    write_episodes_csv(records, RESULTS / "episodes.csv")
    write_summary_csv(summaries, RESULTS / "summary.csv")

    print(f"{'tier':5} {'config':10} {'n':>3} {'catch_rate':>11} {'gotaway/ACH':>12} {'gotaway/all':>12}  attribution")
    for s in summaries:
        attr = ";".join(f"{k}={v}" for k, v in s.attribution.items())
        print(
            f"{s.tier:5} {s.controller_config:10} {s.n:>3} {s.catch_rate:>11.3f} "
            f"{s.got_away_rate:>12.3f} {s.got_away_rate_all:>12.3f}  {attr}"
        )
    print(f"\nwrote {RESULTS/'episodes.csv'} and {RESULTS/'summary.csv'}")


if __name__ == "__main__":
    main()
