#!/usr/bin/env python3
"""Lightweight load/latency smoke test against a running JARVIS backend.

Not part of the pytest suite: perf numbers are environment-dependent (CPU,
network, whatever else is running on the machine) and not a pass/fail
correctness gate, so this is a standalone script you run deliberately,
not something CI enforces a threshold on. It's meant to catch gross
regressions (a change that makes /health 10x slower) when you run it
before/after a change you suspect affects the hot path — not to be a
calibrated benchmark.

Point it at an already-running backend — `make dev` (with a real or
`fakeredis`-free Redis), `docker compose up`, or a deployed instance —
this script does not manage the backend's lifecycle itself, the same way
`ab`/`wrk`/`k6` don't start the server they're pointed at.

Usage:
    python scripts/perf_smoke.py --base-url http://localhost:8000
    python scripts/perf_smoke.py --base-url http://localhost:8000 \\
        --requests 500 --concurrency 50
    python scripts/perf_smoke.py --base-url http://localhost:8000 --ws-chat

    --ws-chat drives real WS /ws/chat turns end to end. If the target
    backend has a real ANTHROPIC_API_KEY configured, this makes real
    Anthropic API calls — real latency, real cost. Point at a backend
    wired to a fake/local LLM endpoint (see tests/e2e/conftest.py's
    ANTHROPIC_BASE_URL override) for a pure wire-protocol perf number
    instead.
"""

from __future__ import annotations

import argparse
import asyncio
import statistics
import time
from dataclasses import dataclass, field

import httpx
import websockets


@dataclass
class LatencyReport:
    label: str
    latencies_ms: list[float] = field(default_factory=list)
    errors: int = 0

    def summarize(self) -> str:
        if not self.latencies_ms:
            return f"{self.label}: no successful requests ({self.errors} errors)"

        sorted_latencies = sorted(self.latencies_ms)

        def percentile(p: float) -> float:
            index = min(len(sorted_latencies) - 1, int(len(sorted_latencies) * p))
            return sorted_latencies[index]

        return (
            f"{self.label}: n={len(self.latencies_ms)} errors={self.errors} "
            f"mean={statistics.mean(self.latencies_ms):.1f}ms "
            f"p50={percentile(0.50):.1f}ms p95={percentile(0.95):.1f}ms "
            f"p99={percentile(0.99):.1f}ms max={max(self.latencies_ms):.1f}ms"
        )


async def _timed_get(client: httpx.AsyncClient, url: str, report: LatencyReport) -> None:
    start = time.perf_counter()
    try:
        response = await client.get(url)
        response.raise_for_status()
    except (httpx.HTTPError, OSError):
        report.errors += 1
        return
    report.latencies_ms.append((time.perf_counter() - start) * 1000)


async def run_health_load(base_url: str, *, requests: int, concurrency: int) -> LatencyReport:
    report = LatencyReport(label=f"GET /health (n={requests}, concurrency={concurrency})")
    semaphore = asyncio.Semaphore(concurrency)

    async def bounded(client: httpx.AsyncClient) -> None:
        async with semaphore:
            await _timed_get(client, f"{base_url}/health", report)

    async with httpx.AsyncClient(timeout=10) as client:
        start = time.perf_counter()
        await asyncio.gather(*(bounded(client) for _ in range(requests)))
        elapsed = time.perf_counter() - start

    if elapsed > 0:
        print(f"  throughput: {requests / elapsed:.1f} req/s over {elapsed:.2f}s")
    return report


async def _timed_ws_turn(ws_url: str, message: str, report: LatencyReport) -> None:
    start = time.perf_counter()
    try:
        async with websockets.connect(ws_url, proxy=None) as websocket:
            await websocket.send(message)
            await asyncio.wait_for(websocket.recv(), timeout=30)
    except (OSError, TimeoutError, websockets.exceptions.WebSocketException):
        report.errors += 1
        return
    report.latencies_ms.append((time.perf_counter() - start) * 1000)


async def run_ws_chat_load(base_url: str, *, messages: int, concurrency: int) -> LatencyReport:
    ws_url = base_url.replace("http://", "ws://", 1).replace("https://", "wss://", 1) + "/ws/chat"
    report = LatencyReport(label=f"WS /ws/chat turn (n={messages}, concurrency={concurrency})")
    semaphore = asyncio.Semaphore(concurrency)

    async def bounded(index: int) -> None:
        async with semaphore:
            await _timed_ws_turn(ws_url, f"perf smoke test message {index}", report)

    start = time.perf_counter()
    await asyncio.gather(*(bounded(i) for i in range(messages)))
    elapsed = time.perf_counter() - start

    if elapsed > 0:
        print(f"  throughput: {messages / elapsed:.1f} turns/s over {elapsed:.2f}s")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--base-url", required=True, help="Running backend base URL, e.g. http://localhost:8000"
    )
    parser.add_argument("--requests", type=int, default=200, help="Number of GET /health requests")
    parser.add_argument(
        "--concurrency", type=int, default=20, help="Max concurrent /health requests"
    )
    parser.add_argument(
        "--ws-chat", action="store_true", help="Also load-test WS /ws/chat (see module docstring)"
    )
    parser.add_argument("--ws-messages", type=int, default=20, help="Number of /ws/chat turns")
    parser.add_argument(
        "--ws-concurrency", type=int, default=5, help="Max concurrent /ws/chat connections"
    )
    args = parser.parse_args()

    print(f"Target: {args.base_url}\n")

    print("GET /health load:")
    health_report = asyncio.run(
        run_health_load(args.base_url, requests=args.requests, concurrency=args.concurrency)
    )
    print(f"  {health_report.summarize()}\n")

    if args.ws_chat:
        print("WS /ws/chat load:")
        chat_report = asyncio.run(
            run_ws_chat_load(
                args.base_url, messages=args.ws_messages, concurrency=args.ws_concurrency
            )
        )
        print(f"  {chat_report.summarize()}")


if __name__ == "__main__":
    main()
