"""Render the degradation-curve figure from the sweep artifacts.

Reads ``results/summary.csv`` and ``results/erosion.csv`` (run ``scripts/run_sweep.py`` first) and
writes ``results/degradation_curve.png``: two panels — catch-rate and survived-rate across the
adversary tiers, one line per controller config — with the composition layer's advantage annotated.
The PNG is rendered from the deterministic CSVs; PNG creation-time metadata is suppressed so repeated
renders of the same CSVs are byte-identical.

Run:  python scripts/make_figures.py [--out PATH]
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
TIER_ORDER = ["T0", "T1", "T2"]
BASELINE = "baseline"
COMPOSITION = "baseline+composition"


def _load_summary(path: Path) -> dict[tuple[str, str], dict]:
    if not path.exists():
        sys.exit(f"missing {path} — run `python scripts/run_sweep.py` first")
    rows = {}
    for r in csv.DictReader(path.open(encoding="utf-8")):
        rows[(r["tier"], r["controller_config"])] = r
    return rows


def _series(summary: dict, config: str, field: str) -> tuple[list[str], list[float]]:
    tiers = [t for t in TIER_ORDER if (t, config) in summary]
    return tiers, [float(summary[(t, config)][field]) for t in tiers]


def render(out: Path, results_dir: Path = RESULTS) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    summary = _load_summary(results_dir / "summary.csv")

    fig, (ax_catch, ax_surv) = plt.subplots(1, 2, figsize=(11, 4.2))

    for ax, field, title, ylabel in [
        (ax_catch, "catch_rate", "Catch-rate degradation", "catch-rate (fraction of lies caught)"),
        (ax_surv, "survived_rate", "Cost: lies that survived all oversight", "survived-rate"),
    ]:
        for config, style in [(BASELINE, "o--"), (COMPOSITION, "o-")]:
            tiers, ys = _series(summary, config, field)
            label = "per-evaluator baseline" if config == BASELINE else "baseline + composition"
            ax.plot(tiers, ys, style, label=label, linewidth=2, markersize=7)
        ax.set_title(title)
        ax.set_xlabel("adversary tier (knowledge ->)")
        ax.set_ylabel(ylabel)
        ax.set_ylim(-0.05, 1.05)
        ax.grid(True, alpha=0.3)
        ax.legend(loc="center left")

    # Annotate the composition advantage on the catch panel.
    tiers, base = _series(summary, BASELINE, "catch_rate")
    _, comp = _series(summary, COMPOSITION, "catch_rate")
    for t, b, c in zip(tiers, base, comp):
        adv = c - b
        if adv > 0:
            ax_catch.annotate(
                f"+{adv:.2f}", xy=(t, (b + c) / 2), xytext=(6, 0), textcoords="offset points",
                va="center", fontsize=10, color="#22863a", fontweight="bold",
            )

    fig.suptitle("Correct-shaped lies — oversight erosion across adversary tiers", fontsize=13)
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    # metadata={} drops the default PNG creation-time chunk -> byte-stable across renders.
    fig.savefig(out, dpi=130, metadata={"Software": None})
    plt.close(fig)
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=RESULTS / "degradation_curve.png")
    args = parser.parse_args()
    path = render(args.out)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
