"""
🔐 Security helpers for encryption.
"""
from __future__ import annotations

from cryptography.fernet import Fernet

from core.config import settings


def _get_cipher() -> Fernet:
    if not settings.integrations_enc_key:
        raise ValueError("INTEGRATIONS_ENC_KEY not configured")
    return Fernet(settings.integrations_enc_key)


def encrypt_secret(value: str) -> str:
    cipher = _get_cipher()
    return cipher.encrypt(value.encode()).decode()


def decrypt_secret(encrypted: str) -> str:
    cipher = _get_cipher()
    return cipher.decrypt(encrypted.encode()).decode()
