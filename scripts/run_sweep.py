"""Run the full catch-rate sweep (baseline vs baseline+composition) and write artifacts.

Uses the deterministic :class:`ScriptedProducer` (no API key needed), drives every episode through
the real Go controller + ML service, scores each under both controller configs, and writes:

* ``results/episodes.csv`` — one row per (episode, config);
* ``results/summary.csv``  — catch-rate, survived-rate, got-away, attribution per (tier, config);
* ``results/erosion.csv``  — the composition layer's catch-rate advantage per tier.

Run:  python scripts/run_sweep.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from csl.composition import CompositionLayer, build_reference
from csl.controller.harness import running_stack
from csl.domain.registry import get_domain
from csl.experiment.artifacts import write_episodes_csv, write_summary_csv
from csl.experiment.config import SweepConfig
from csl.experiment.metrics import erosion_test, summarize
from csl.experiment.runner import ExperimentRunner
from csl.producer.scripted import ScriptedProducer

RESULTS = Path(__file__).resolve().parents[1] / "results"


def _write_erosion_csv(rows, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["tier", "catch_baseline", "catch_composition", "composition_advantage", "survived_baseline", "survived_composition"]
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(
                {
                    "tier": r.tier,
                    "catch_baseline": f"{r.catch_baseline:.4f}",
                    "catch_composition": f"{r.catch_composition:.4f}",
                    "composition_advantage": f"{r.composition_advantage:.4f}",
                    "survived_baseline": f"{r.survived_baseline:.4f}",
                    "survived_composition": f"{r.survived_composition:.4f}",
                }
            )
    return path


def main() -> None:
    config = SweepConfig()
    domain = get_domain(config.domain_name, honesty_seed=config.honesty_seed)
    producer = ScriptedProducer()
    reference = build_reference(domain, ScriptedProducer(force_strategy="honest"))
    composition = CompositionLayer.default(reference)

    with running_stack() as client:
        records = ExperimentRunner(config, producer, domain, client, composition_layer=composition).run()

    summaries = summarize(records)
    erosion = erosion_test(summaries)
    write_episodes_csv(records, RESULTS / "episodes.csv")
    write_summary_csv(summaries, RESULTS / "summary.csv")
    _write_erosion_csv(erosion, RESULTS / "erosion.csv")

    print(f"{'tier':5} {'config':22} {'n':>3} {'catch':>7} {'survived':>9} {'gotaway/all':>12}  attribution")
    for s in summaries:
        attr = ";".join(f"{k}={v}" for k, v in s.attribution.items())
        print(
            f"{s.tier:5} {s.controller_config:22} {s.n:>3} {s.catch_rate:>7.3f} "
            f"{s.survived_rate:>9.3f} {s.got_away_rate_all:>12.3f}  {attr}"
        )

    print("\nErosion test - composition layer's catch-rate advantage by tier:")
    print(f"{'tier':5} {'baseline':>9} {'+composition':>13} {'advantage':>10} {'survived(base->comp)':>22}")
    for r in erosion:
        print(
            f"{r.tier:5} {r.catch_baseline:>9.3f} {r.catch_composition:>13.3f} "
            f"{r.composition_advantage:>10.3f}   {r.survived_baseline:>8.3f} -> {r.survived_composition:.3f}"
        )
    print(f"\nwrote {RESULTS/'episodes.csv'}, {RESULTS/'summary.csv'}, {RESULTS/'erosion.csv'}")


if __name__ == "__main__":
    main()
