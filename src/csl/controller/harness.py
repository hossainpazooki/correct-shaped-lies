"""Start the full controller stack (Go lifecycle controller + Python ML service) for a run.

``running_stack()`` is a context manager that:

1. starts the FastAPI ML service in a daemon uvicorn thread (in-process, sharing the episode
   registry), then
2. builds and launches the Go controller as a subprocess pointed at the ML service, then
3. waits for both to report healthy and yields a :class:`ControllerClient`.

Teardown stops both. Ports are chosen free at start. Everything in the measured path is
deterministic; only process startup is non-deterministic, and it does not touch episode state.
"""

from __future__ import annotations

import contextlib
import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

from csl.controller.client import ControllerClient
from csl.controller.ml_service import REGISTRY, create_app

_REPO_ROOT = Path(__file__).resolve().parents[3]
_CONTROLLER_DIR = _REPO_ROOT / "intent-controller"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _build_controller() -> Path:
    """Build the Go controller binary once; return its path. Raises if Go/build unavailable."""
    binary = _CONTROLLER_DIR / ("bin/server.exe" if sys.platform == "win32" else "bin/server")
    binary.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        ["go", "build", "-o", str(binary), "./cmd/server"],
        cwd=_CONTROLLER_DIR,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"go build failed:\n{proc.stderr}")
    return binary


class _UvicornThread:
    def __init__(self, app, port: int) -> None:
        import uvicorn

        self._config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
        self._server = uvicorn.Server(self._config)
        self._thread = threading.Thread(target=self._server.run, daemon=True)

    def start(self, timeout: float = 10.0) -> None:
        self._thread.start()
        deadline = time.monotonic() + timeout
        while not self._server.started:
            if time.monotonic() > deadline:
                raise RuntimeError("ML service did not start in time")
            time.sleep(0.02)

    def stop(self) -> None:
        self._server.should_exit = True
        self._thread.join(timeout=5.0)


@contextlib.contextmanager
def running_stack(registry=REGISTRY, startup_timeout: float = 15.0):
    """Yield a :class:`ControllerClient` connected to a live Go controller + ML service."""
    ml_port = _free_port()
    ctrl_port = _free_port()

    app = create_app(registry)
    ml = _UvicornThread(app, ml_port)
    ml.start()

    binary = _build_controller()
    # Inherit the full environment (Windows Winsock needs SystemRoot et al.) and override only ours.
    env = {**os.environ, "PORT": str(ctrl_port), "ML_SERVICE_URL": f"http://127.0.0.1:{ml_port}"}
    proc = subprocess.Popen([str(binary)], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    client = ControllerClient(f"http://127.0.0.1:{ctrl_port}")
    try:
        _await_health(client, proc, deadline=time.monotonic() + startup_timeout)
        yield client
    finally:
        client.close()
        proc.terminate()
        with contextlib.suppress(subprocess.TimeoutExpired):
            proc.wait(timeout=5.0)
        ml.stop()


def _await_health(client: ControllerClient, proc: subprocess.Popen, deadline: float) -> None:
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            err = proc.stderr.read().decode() if proc.stderr else ""
            raise RuntimeError(f"controller exited early (code {proc.returncode}):\n{err}")
        if client.health():
            return
        time.sleep(0.05)
    raise RuntimeError("controller did not become healthy in time")
