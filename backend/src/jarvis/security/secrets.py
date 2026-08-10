"""Encryption at rest for API keys and credentials.

Derives a Fernet key deterministically from `Settings.secret_key` via
SHA-256, so operators manage one secret (`JARVIS_SECRET_KEY`) rather than a
separate encryption key to provision and rotate.
"""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from jarvis.core.exceptions import ValidationError


def _derive_fernet_key(secret_key: str) -> bytes:
    digest = hashlib.sha256(secret_key.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


class SecretsVault:
    """Encrypts/decrypts small values (API keys, tokens) at rest.

    Not a general-purpose secret manager: values pass through this vault to
    be stored (in Postgres, plugin config, ...) and are decrypted only at
    the point of use — never logged, never returned verbatim over the API.
    """

    def __init__(self, secret_key: str) -> None:
        self._fernet = Fernet(_derive_fernet_key(secret_key))

    def encrypt(self, plaintext: str) -> str:
        return self._fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        try:
            return self._fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:
            raise ValidationError("could not decrypt secret: invalid token or wrong key") from exc
