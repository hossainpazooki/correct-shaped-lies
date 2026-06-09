"""Resource-bounded subprocess executor for candidate code.

Candidate submissions are executed in a fresh Python subprocess with a wall-clock timeout, in
isolated mode (``-I``) so the host environment and ``PYTHONPATH`` cannot leak in. Inputs and outputs
cross the boundary as JSON, so only JSON-serializable values are supported (ints, floats, strings,
bools, lists, dicts) — which is all the reference domain needs. Execution is a pure function of
``(code, func_name, inputs)``: no randomness, no clock, deterministic.

This is research code that deliberately runs author-controlled producers; the subprocess + timeout is
isolation for reproducibility and runaway protection, not a security boundary against hostile code.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

#: Marker the runner prints before its JSON payload, so we can ignore any incidental stdout.
_MARKER = "__CSL_RESULT__"

_RUNNER_TEMPLATE = '''\
import json, sys

{code}

def _csl_run():
    payload = json.loads(sys.stdin.read())
    func = globals().get(payload["func"])
    out = []
    if func is None:
        for _ in payload["inputs"]:
            out.append({{"ok": False, "error": "function {func_name!r} not defined"}})
    else:
        for args in payload["inputs"]:
            try:
                val = func(*args)
                json.dumps(val)  # ensure serializable before claiming success
                out.append({{"ok": True, "value": val}})
            except Exception as exc:  # noqa: BLE001 - report any failure as a per-input error
                out.append({{"ok": False, "error": repr(exc)}})
    sys.stdout.write({marker!r} + json.dumps(out))

_csl_run()
'''


@dataclass(frozen=True)
class SandboxResult:
    """Outcome of running the function on one input."""

    ok: bool
    value: object = None
    error: str | None = None
    timed_out: bool = False


def run_batch(
    code: str,
    func_name: str,
    inputs: list[tuple],
    timeout: float = 5.0,
) -> list[SandboxResult]:
    """Run ``func_name`` over every input tuple in one subprocess; one result per input.

    A timeout, crash, or missing function maps every input to a failed :class:`SandboxResult` (with
    ``timed_out=True`` on timeout). Per-input exceptions are caught individually.
    """
    source = _RUNNER_TEMPLATE.format(
        code=code,
        func_name=func_name,
        marker=_MARKER,
    )
    payload = json.dumps({"func": func_name, "inputs": [list(args) for args in inputs]})

    with tempfile.TemporaryDirectory() as tmp:
        runner_path = Path(tmp) / "runner.py"
        runner_path.write_text(source, encoding="utf-8")
        try:
            proc = subprocess.run(
                [sys.executable, "-I", str(runner_path)],
                input=payload,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return [SandboxResult(ok=False, error="timeout", timed_out=True) for _ in inputs]

    out = proc.stdout
    idx = out.rfind(_MARKER)
    if idx == -1:
        err = (proc.stderr or "no output").strip()
        return [SandboxResult(ok=False, error=f"runner error: {err}") for _ in inputs]

    decoded = json.loads(out[idx + len(_MARKER):])
    results: list[SandboxResult] = []
    for item in decoded:
        if item.get("ok"):
            results.append(SandboxResult(ok=True, value=item.get("value")))
        else:
            results.append(SandboxResult(ok=False, error=item.get("error")))
    return results


def run_one(code: str, func_name: str, args: tuple, timeout: float = 5.0) -> SandboxResult:
    """Convenience: run a single input."""
    return run_batch(code, func_name, [args], timeout=timeout)[0]
