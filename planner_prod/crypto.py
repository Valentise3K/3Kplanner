import base64

from cryptography.fernet import Fernet

from config import settings

_fernet = Fernet(settings.ENCRYPTION_KEY.encode() if len(settings.ENCRYPTION_KEY) < 44
                 else settings.ENCRYPTION_KEY.encode())


def encrypt(value: str) -> str:
    """Encrypt a string value for storage."""
    return _fernet.encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    """Decrypt a stored encrypted string."""
    try:
        return _fernet.decrypt(value.encode()).decode()
    except Exception:
        return value
