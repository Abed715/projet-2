"""Fixtures for out-of-process, full-stack e2e tests: a real `redis-server`
subprocess, a real `uvicorn` subprocess running the actual FastAPI app (a
genuine OS process listening on a real socket - not `TestClient`), and a
minimal fake HTTP server standing in for Anthropic's API so a real chat
round trip can be driven with no real API key and no real network call to
Anthropic. See README.md in this directory for why each piece exists.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

import httpx
import pytest


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_port(host: str, port: int, *, timeout_seconds: float) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError(f"nothing listening on {host}:{port} after {timeout_seconds}s")


@pytest.fixture(scope="session")
def redis_port() -> Iterator[int]:
    """A real `redis-server`, freshly started on an ephemeral port -
    self-contained, no dependency on a pre-existing service container.
    """
    port = _free_port()
    process = subprocess.Popen(
        ["redis-server", "--port", str(port), "--save", "", "--appendonly", "no"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_for_port("127.0.0.1", port, timeout_seconds=10)
        yield port
    finally:
        process.terminate()
        process.wait(timeout=5)


class _FakeAnthropicHandler(BaseHTTPRequestHandler):
    """Responds to POST /v1/messages the way `anthropic.AsyncAnthropic`
    expects, echoing the last user message back so tests can assert the
    real request payload reached here unmodified.
    """

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        pass  # silence BaseHTTPRequestHandler's default stderr logging

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))
        self.server.received_requests.append(body)  # type: ignore[attr-defined]

        last_message = body.get("messages", [{}])[-1]
        content = last_message.get("content", "")
        last_user_text = content if isinstance(content, str) else str(content)

        response_body = {
            "id": "msg_fake_e2e",
            "type": "message",
            "role": "assistant",
            "model": body.get("model", "fake-model"),
            "content": [{"type": "text", "text": f"echo: {last_user_text}"}],
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {"input_tokens": 1, "output_tokens": 1},
        }
        payload = json.dumps(response_body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


@pytest.fixture
def fake_anthropic_server() -> Iterator[tuple[str, list[dict[str, object]]]]:
    """Yields `(base_url, received_requests)` - `received_requests` is a
    live list the handler appends to, so tests can assert on what the
    real backend process actually sent.
    """
    server = ThreadingHTTPServer(("127.0.0.1", 0), _FakeAnthropicHandler)
    server.received_requests = []  # type: ignore[attr-defined]
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host = "127.0.0.1"
    port = server.server_address[1]
    try:
        yield f"http://{host}:{port}", server.received_requests  # type: ignore[attr-defined]
    finally:
        server.shutdown()
        thread.join(timeout=5)


@pytest.fixture
def backend_base_url(
    redis_port: int,
    fake_anthropic_server: tuple[str, list[dict[str, object]]],
    tmp_path: Path,
) -> Iterator[str]:
    """Launches the real `jarvis.api.app:create_app` factory under a real
    `uvicorn` subprocess - the same command `docker/backend.Dockerfile`
    runs - pointed at the ephemeral Redis and the fake Anthropic server
    above via real environment variables, exactly as a real deployment
    would be configured.
    """
    anthropic_base_url, _requests = fake_anthropic_server
    app_port = _free_port()
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()

    env = os.environ.copy()
    env.update(
        {
            "JARVIS_ENV": "test",
            "JARVIS_SECRET_KEY": "e2e-test-secret",
            "JARVIS_WORKSPACE_DIR": str(workspace_dir),
            "REDIS_HOST": "127.0.0.1",
            "REDIS_PORT": str(redis_port),
            "ANTHROPIC_API_KEY": "sk-ant-fake-e2e-key",
            "ANTHROPIC_BASE_URL": anthropic_base_url,
            "JARVIS_ANTHROPIC_MODEL": "fake-e2e-model",
        }
    )

    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "jarvis.api.app:create_app",
            "--factory",
            "--host",
            "127.0.0.1",
            "--port",
            str(app_port),
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    base_url = f"http://127.0.0.1:{app_port}"
    try:
        deadline = time.monotonic() + 15
        healthy = False
        while time.monotonic() < deadline:
            if process.poll() is not None:
                output = process.stdout.read() if process.stdout else ""
                raise RuntimeError(f"backend process exited early:\n{output}")
            try:
                response = httpx.get(f"{base_url}/health", timeout=1)
                if response.status_code == 200:
                    healthy = True
                    break
            except httpx.HTTPError:
                pass
            time.sleep(0.2)
        if not healthy:
            process.terminate()
            raise RuntimeError("backend did not become healthy in time")
        yield base_url
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
