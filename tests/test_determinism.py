"""W1-3: byte-identical-per-seed determinism for task sampling and evaluators."""

from __future__ import annotations

from csl.domain.base import Submission
from csl.domain.code_generation import CodeGenerationDomain
from csl.seeding import make_rng

HONEST_ADD = "def solve(a, b):\n    return a + b\n"


def _sample_ids(seed: int, n: int) -> list[str]:
    domain = CodeGenerationDomain()
    tasks = domain.sample_tasks(make_rng(seed), n)
    return [t.task_id for t in tasks]


def test_task_sampling_is_deterministic():
    assert _sample_ids(123, 10) == _sample_ids(123, 10)


def test_different_seeds_differ():
    # Not a hard guarantee in general, but the corpus + draw make these two seeds differ.
    assert _sample_ids(1, 10) != _sample_ids(2, 10)


def test_honesty_probe_is_deterministic():
    domain = CodeGenerationDomain(honesty_seed=99, n_honesty_probes=32)
    task = domain.task("count_vowels")
    honesty = {e.name: e for e in domain.evaluators()}["honesty"]
    sub = Submission(code="def solve(s):\n    return sum(c in 'aeiou' for c in s.lower())\n")

    first = honesty.evaluate(sub, task)
    second = honesty.evaluate(sub, task)
    assert first.score == second.score == 1.0
    assert first.details["n_probes"] == second.details["n_probes"] == 32
