import pytest

from jarvis.core.exceptions import ValidationError
from jarvis.security.secrets import SecretsVault


def test_encrypt_then_decrypt_roundtrips() -> None:
    vault = SecretsVault(secret_key="test-secret")

    ciphertext = vault.encrypt("super-secret-api-key")

    assert ciphertext != "super-secret-api-key"
    assert vault.decrypt(ciphertext) == "super-secret-api-key"


def test_different_keys_produce_undecryptable_ciphertext() -> None:
    vault_a = SecretsVault(secret_key="key-a")
    vault_b = SecretsVault(secret_key="key-b")

    ciphertext = vault_a.encrypt("hello")

    with pytest.raises(ValidationError):
        vault_b.decrypt(ciphertext)


def test_decrypting_garbage_raises_validation_error() -> None:
    vault = SecretsVault(secret_key="test-secret")

    with pytest.raises(ValidationError):
        vault.decrypt("not-a-real-token")


def test_same_key_is_deterministic_across_instances() -> None:
    vault_1 = SecretsVault(secret_key="stable-key")
    vault_2 = SecretsVault(secret_key="stable-key")

    ciphertext = vault_1.encrypt("payload")

    assert vault_2.decrypt(ciphertext) == "payload"
