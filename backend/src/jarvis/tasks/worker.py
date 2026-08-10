"""TaskWorker: a thin poll loop over `TaskEngine.run_once`. Production
code drives this continuously via `run()`; tests call
`TaskEngine.run_once` directly for deterministic, one-task-at-a-time
control instead of racing a background loop.
"""

from __future__ import annotations

import asyncio

from jarvis.tasks.engine import TaskEngine

DEFAULT_POLL_INTERVAL_SECONDS = 1.0


class TaskWorker:
    def __init__(
        self,
        engine: TaskEngine,
        *,
        consumer_name: str,
        poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS,
    ) -> None:
        self._engine = engine
        self._consumer_name = consumer_name
        self._poll_interval_seconds = poll_interval_seconds

    async def run(self, stop_event: asyncio.Event) -> None:
        """Process tasks until `stop_event` is set. Sleeps between polls
        only when the queue was empty, so a burst of pending work drains
        back-to-back.
        """
        while not stop_event.is_set():
            task = await self._engine.run_once(self._consumer_name)
            if task is None:
                await asyncio.sleep(self._poll_interval_seconds)
