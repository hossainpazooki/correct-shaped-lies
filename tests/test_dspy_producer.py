"""DSPy producer smoke test — skipped unless ``dspy`` is installed.

Uses DSPy's DummyLM (no network/API) to return a canned submission, verifying the producer wires the
brief through and returns a usable :class:`Submission`. Live optimization (MIPROv2) needs a real LM
and is exercised in the API-driven sweep, not here.
"""

from __future__ import annotations

import importlib.util

import pytest

from csl.domain.code_generation import CodeGenerationDomain

pytestmark = pytest.mark.skipif(importlib.util.find_spec("dspy") is None, reason="dspy not installed")


def test_dspy_producer_returns_submission():
    import dspy

    from csl.producer.agent import DSPyProducer

    domain = CodeGenerationDomain(honesty_seed=7)
    task = domain.task("add_two")

    canned = "```python\ndef solve(a, b):\n    return a + b\n```"
    lm = dspy.utils.DummyLM([{"submission": canned, "reasoning": "n/a"}])

    producer = DSPyProducer(domain, lm=lm)
    submission = producer.produce(task, "T1")

    assert "def solve" in submission.code
    passed, score, _ = domain.main_task_checker().check(submission, task)
    assert passed and score == 1.0
