import json

from cryptography.fernet import Fernet

from app.config import get_settings


def encrypt_storage_state(storage_state: dict) -> bytes:
    fernet = Fernet(get_settings().session_encryption_key)
    payload = json.dumps(storage_state).encode()
    return fernet.encrypt(payload)


def decrypt_storage_state(encrypted: bytes) -> dict:
    fernet = Fernet(get_settings().session_encryption_key)
    payload = fernet.decrypt(encrypted)
    return json.loads(payload)
