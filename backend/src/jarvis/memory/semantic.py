"""Semantic (vector) memory: similarity search over embedded text chunks.
Backed by ChromaDB.

Embeddings are supplied by the caller — the embedding provider lives in
`jarvis.brain` (Phase 2), behind the same `LLMProvider`-style abstraction as
chat completions. This module only stores and searches vectors; it never
calls out to an embedding model itself, which keeps it usable offline and
in tests with no network access.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, cast

import chromadb
from chromadb.api import ClientAPI


@dataclass(frozen=True, slots=True)
class SemanticMatch:
    id: str
    text: str
    metadata: dict[str, str]
    distance: float


def create_ephemeral_client() -> ClientAPI:
    """In-process, non-persistent Chroma client — used in tests and by
    default in local dev when no Chroma server is configured.
    """
    return chromadb.EphemeralClient()


def create_http_client(host: str, port: int) -> ClientAPI:
    """Client for the `chroma` service in `docker-compose.yml`."""
    return chromadb.HttpClient(host=host, port=port)


class SemanticMemory:
    """Wraps a single ChromaDB collection (one namespace, e.g. one user)."""

    def __init__(self, client: ClientAPI, *, collection_name: str = "jarvis_memory") -> None:
        self._collection = client.get_or_create_collection(collection_name)

    def add(
        self,
        *,
        text: str,
        embedding: list[float],
        metadata: dict[str, str] | None = None,
        id: str | None = None,
    ) -> str:
        record_id = id or str(uuid.uuid4())
        # chromadb's stubs accept numpy arrays or Sequence[float] in a way
        # that doesn't line up with a plain list[list[float]] under mypy's
        # invariance rules; `Any` here is a deliberate boundary cast, not a
        # loss of type-safety for callers (SemanticMemory's own signature
        # stays fully typed).
        self._collection.add(
            ids=[record_id],
            embeddings=cast(Any, [embedding]),
            documents=[text],
            metadatas=[metadata] if metadata else None,
        )
        return record_id

    def query(self, *, embedding: list[float], top_k: int = 5) -> list[SemanticMatch]:
        result = self._collection.query(
            query_embeddings=cast(Any, [embedding]), n_results=top_k
        )

        ids = result["ids"][0]
        documents = result["documents"][0] if result["documents"] else [""] * len(ids)
        metadatas = result["metadatas"][0] if result["metadatas"] else [{}] * len(ids)
        distances = result["distances"][0] if result["distances"] else [0.0] * len(ids)

        return [
            SemanticMatch(
                id=ids[i],
                text=documents[i] or "",
                metadata={str(k): str(v) for k, v in (metadatas[i] or {}).items()},
                distance=distances[i],
            )
            for i in range(len(ids))
        ]

    def delete(self, id: str) -> None:
        self._collection.delete(ids=[id])
