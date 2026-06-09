"""Reproducibility: byte-identical CSV artifacts and a byte-identical figure render."""

from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path

import pytest

from csl.experiment.artifacts import write_episodes_csv, write_summary_csv
from csl.experiment.metrics import BASELINE, COMPOSITION, EpisodeRecord, summarize

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def _records():
    return [
        EpisodeRecord("T0", "add_two", 0, BASELINE, "failed", False, True, ("static_safety",)),
        EpisodeRecord("T1", "add_two", 0, BASELINE, "achieved", True, True, ()),
        EpisodeRecord("T1", "add_two", 0, COMPOSITION, "achieved", True, True, ("cross_stage_consistency",)),
        EpisodeRecord("T2", "add_two", 0, COMPOSITION, "achieved", True, True, ()),
    ]


def test_csv_writers_are_byte_deterministic(tmp_path):
    recs = _records()
    summaries = summarize(recs)

    e1 = write_episodes_csv(recs, tmp_path / "ep1.csv")
    e2 = write_episodes_csv(recs, tmp_path / "ep2.csv")
    s1 = write_summary_csv(summaries, tmp_path / "su1.csv")
    s2 = write_summary_csv(summaries, tmp_path / "su2.csv")

    assert e1.read_bytes() == e2.read_bytes()
    assert s1.read_bytes() == s2.read_bytes()


@pytest.mark.skipif(importlib.util.find_spec("matplotlib") is None, reason="matplotlib not installed")
def test_figure_render_is_byte_deterministic(tmp_path):
    import make_figures  # from scripts/, on sys.path

    write_summary_csv(summarize(_records()), tmp_path / "summary.csv")
    a = make_figures.render(tmp_path / "a.png", results_dir=tmp_path)
    b = make_figures.render(tmp_path / "b.png", results_dir=tmp_path)
    assert a.read_bytes() == b.read_bytes()


@pytest.mark.skipif(shutil.which("go") is None, reason="Go toolchain not available")
def test_full_sweep_artifacts_byte_identical(tmp_path):
    """Two sweeps through the real controller produce byte-identical CSV artifacts."""
    from csl.composition import CompositionLayer, build_reference
    from csl.controller.harness import running_stack
    from csl.domain.code_generation import CodeGenerationDomain
    from csl.experiment.config import SweepConfig
    from csl.experiment.runner import ExperimentRunner
    from csl.producer.scripted import ScriptedProducer

    config = SweepConfig(tiers=("T1", "T2"), seeds=(0,))
    domain = CodeGenerationDomain(honesty_seed=0)
    layer = CompositionLayer.default(build_reference(domain, ScriptedProducer(force_strategy="honest")))

    def one_run(tag: str) -> bytes:
        with running_stack() as client:
            records = ExperimentRunner(config, ScriptedProducer(), domain, client, composition_layer=layer).run()
        path = write_episodes_csv(records, tmp_path / f"episodes_{tag}.csv")
        return path.read_bytes()

    assert one_run("a") == one_run("b")
