from jarvis.core.redis import create_redis_client


def test_create_redis_client_builds_from_url() -> None:
    client = create_redis_client("redis://localhost:6379/0")

    assert client.connection_pool.connection_kwargs["host"] == "localhost"
    assert client.connection_pool.connection_kwargs["port"] == 6379
    assert client.connection_pool.connection_kwargs["db"] == 0


def test_create_redis_client_decodes_responses() -> None:
    client = create_redis_client("redis://localhost:6379/1")

    assert client.connection_pool.connection_kwargs["decode_responses"] is True
