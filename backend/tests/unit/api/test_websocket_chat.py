from fastapi.testclient import TestClient

from jarvis.agents.base import AgentReply
from jarvis.api.app import create_app


class _FakeAgent:
    """Satisfies the `Agent` interface `create_app` needs, with no network."""

    def __init__(self) -> None:
        self.received: list[tuple[str, str]] = []

    async def respond(self, session_id: str, user_message: str) -> AgentReply:
        self.received.append((session_id, user_message))
        return AgentReply(content=f"echo: {user_message}")


def test_chat_websocket_round_trip() -> None:
    fake_agent = _FakeAgent()
    app = create_app(coordinator=fake_agent)  # type: ignore[arg-type]
    client = TestClient(app)

    with client.websocket_connect("/ws/chat") as websocket:
        websocket.send_text("hello")
        reply = websocket.receive_text()

    assert reply == "echo: hello"


def test_chat_websocket_maintains_one_session_per_connection() -> None:
    fake_agent = _FakeAgent()
    app = create_app(coordinator=fake_agent)  # type: ignore[arg-type]
    client = TestClient(app)

    with client.websocket_connect("/ws/chat") as websocket:
        websocket.send_text("first")
        websocket.receive_text()
        websocket.send_text("second")
        websocket.receive_text()

    session_ids = {session_id for session_id, _ in fake_agent.received}
    assert len(session_ids) == 1
    assert [msg for _, msg in fake_agent.received] == ["first", "second"]


def test_chat_websocket_uses_distinct_sessions_per_connection() -> None:
    fake_agent = _FakeAgent()
    app = create_app(coordinator=fake_agent)  # type: ignore[arg-type]
    client = TestClient(app)

    with client.websocket_connect("/ws/chat") as ws1:
        ws1.send_text("a")
        ws1.receive_text()

    with client.websocket_connect("/ws/chat") as ws2:
        ws2.send_text("b")
        ws2.receive_text()

    session_ids = [session_id for session_id, _ in fake_agent.received]
    assert session_ids[0] != session_ids[1]


def test_create_app_without_coordinator_still_boots() -> None:
    # No coordinator override: create_app must not perform any network I/O
    # at construction time (Redis/Anthropic clients are lazy) — only /health
    # is exercised here, not /ws/chat, which would require live services.
    app = create_app()
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
