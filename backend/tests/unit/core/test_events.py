import pytest

from jarvis.core.events import Event, InMemoryEventBus


@pytest.mark.asyncio
async def test_publish_calls_matching_subscriber() -> None:
    bus = InMemoryEventBus()
    received: list[Event] = []

    async def handler(event: Event) -> None:
        received.append(event)

    bus.subscribe("memory.candidate", handler)
    await bus.publish(Event(topic="memory.candidate", payload={"fact": "likes tea"}))

    assert len(received) == 1
    assert received[0].payload == {"fact": "likes tea"}


@pytest.mark.asyncio
async def test_publish_ignores_unrelated_topics() -> None:
    bus = InMemoryEventBus()
    received: list[Event] = []

    async def handler(event: Event) -> None:
        received.append(event)

    bus.subscribe("topic.a", handler)
    await bus.publish(Event(topic="topic.b"))

    assert received == []


@pytest.mark.asyncio
async def test_publish_with_no_subscribers_is_a_noop() -> None:
    bus = InMemoryEventBus()

    await bus.publish(Event(topic="nobody.listening"))  # should not raise


@pytest.mark.asyncio
async def test_all_subscribers_receive_the_event() -> None:
    bus = InMemoryEventBus()
    counter = {"a": 0, "b": 0}

    async def handler_a(event: Event) -> None:
        counter["a"] += 1

    async def handler_b(event: Event) -> None:
        counter["b"] += 1

    bus.subscribe("topic", handler_a)
    bus.subscribe("topic", handler_b)
    await bus.publish(Event(topic="topic"))

    assert counter == {"a": 1, "b": 1}


@pytest.mark.asyncio
async def test_failing_handler_does_not_break_other_handlers_or_publisher() -> None:
    bus = InMemoryEventBus()
    received: list[str] = []

    async def failing_handler(event: Event) -> None:
        raise RuntimeError("boom")

    async def ok_handler(event: Event) -> None:
        received.append("ok")

    bus.subscribe("topic", failing_handler)
    bus.subscribe("topic", ok_handler)

    await bus.publish(Event(topic="topic"))  # should not raise

    assert received == ["ok"]
