import uuid

import pytest

from jarvis.memory.semantic import SemanticMemory, create_ephemeral_client


@pytest.fixture
def memory() -> SemanticMemory:
    # chromadb caches its in-process system by settings, so a fixed
    # collection name would leak state across tests in the same process —
    # each test gets its own collection to stay isolated.
    client = create_ephemeral_client()
    return SemanticMemory(client, collection_name=f"test_{uuid.uuid4().hex}")


def test_add_returns_an_id(memory: SemanticMemory) -> None:
    record_id = memory.add(text="the user prefers tea", embedding=[1.0, 0.0, 0.0])

    assert record_id


def test_query_finds_the_closest_match(memory: SemanticMemory) -> None:
    memory.add(text="the user prefers tea", embedding=[1.0, 0.0, 0.0], id="tea")
    memory.add(text="the user prefers coffee", embedding=[0.0, 1.0, 0.0], id="coffee")

    matches = memory.query(embedding=[0.9, 0.1, 0.0], top_k=1)

    assert len(matches) == 1
    assert matches[0].id == "tea"
    assert matches[0].text == "the user prefers tea"


def test_query_respects_top_k(memory: SemanticMemory) -> None:
    for i in range(5):
        memory.add(text=f"fact {i}", embedding=[float(i), 0.0, 0.0], id=f"fact-{i}")

    matches = memory.query(embedding=[0.0, 0.0, 0.0], top_k=2)

    assert len(matches) == 2


def test_metadata_is_preserved(memory: SemanticMemory) -> None:
    memory.add(
        text="likes tea", embedding=[1.0, 0.0, 0.0], id="tea", metadata={"kind": "preference"}
    )

    matches = memory.query(embedding=[1.0, 0.0, 0.0], top_k=1)

    assert matches[0].metadata == {"kind": "preference"}


def test_delete_removes_the_record(memory: SemanticMemory) -> None:
    memory.add(text="temp", embedding=[1.0, 0.0, 0.0], id="temp")

    memory.delete("temp")

    matches = memory.query(embedding=[1.0, 0.0, 0.0], top_k=5)
    assert all(match.id != "temp" for match in matches)
