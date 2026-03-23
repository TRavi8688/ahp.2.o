import os
import json
import base64
import hashlib
from sqlalchemy.types import TypeDecorator, String, Text
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.core.config import settings
from app.core.logging import logger

class DecryptionError(Exception):
    """Raised when data decryption fails, indicating a potential key mismatch or data corruption."""
    pass

class StringEncryptedType(TypeDecorator):
    """
    Production-grade AES-GCM encryption for SQLAlchemy string fields.
    Uses a unique 12-byte nonce (IV) for every record to prevent pattern analysis.
    """
    impl = String
    cache_ok = True

    def _get_aesgcm(self):
        """Lazy loader for AES-GCM engine to allow app boot without keys."""
        if not settings.ENCRYPTION_KEY or len(settings.ENCRYPTION_KEY) < 32:
             logger.critical("MISSING_ENCRYPTION_KEY: Data operations will fail.")
             raise ValueError("CRITICAL: ENCRYPTION_KEY not found or too short in environment.")
        
        try:
             key = base64.b64decode(settings.ENCRYPTION_KEY)
             if len(key) != 32:
                  key = hashlib.sha256(settings.ENCRYPTION_KEY.encode()).digest()
             return AESGCM(key)
        except Exception as e:
             logger.critical(f"ENCRYPTION_KEY_FORMAT_ERROR: {e}")
             raise ValueError("CRITICAL: Invalid ENCRYPTION_KEY format.")

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        aesgcm = self._get_aesgcm()
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, value.encode('utf-8'), None)
        return base64.b64encode(nonce + ciphertext).decode('utf-8')

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        try:
             aesgcm = self._get_aesgcm()
             data = base64.b64decode(value.encode('utf-8'))
             nonce = data[:12]
             ciphertext = data[12:]
             return aesgcm.decrypt(nonce, ciphertext, None).decode('utf-8')
        except Exception as e:
             logger.critical(f"DECRYPTION_FAILURE: {e}")
             return "DECRYPTION_ERROR"

class TextEncryptedType(TypeDecorator):
    """AES-GCM encryption for SQLAlchemy Text fields with lazy key loader."""
    impl = Text
    cache_ok = True

    def _get_aesgcm(self):
        if not settings.ENCRYPTION_KEY:
             raise ValueError("CRITICAL: ENCRYPTION_KEY not found in environment.")
        key = hashlib.sha256(settings.ENCRYPTION_KEY.encode()).digest()
        return AESGCM(key)

    def process_bind_param(self, value, dialect):
        if not value: return None
        aesgcm = self._get_aesgcm()
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, value.encode('utf-8'), None)
        return base64.b64encode(nonce + ciphertext).decode('utf-8')

    def process_result_value(self, value, dialect):
        if not value: return None
        try:
            aesgcm = self._get_aesgcm()
            data = base64.b64decode(value.encode('utf-8'))
            nonce = data[:12]
            ciphertext = data[12:]
            return aesgcm.decrypt(nonce, ciphertext, None).decode('utf-8')
        except Exception as e:
            logger.critical(f"DECRYPTION_FAILURE: {e}")
            return "DECRYPTION_ERROR"

def encrypt_value(value: str) -> str:
    """Standalone AES-GCM encryption helper."""
    if not value: return ""
    key = hashlib.sha256(settings.ENCRYPTION_KEY.encode()).digest()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, value.encode('utf-8'), None)
    return base64.b64encode(nonce + ciphertext).decode('utf-8')

def decrypt_value(encrypted_value: str) -> str:
    """Standalone AES-GCM decryption helper."""
    if not encrypted_value: return ""
    key = hashlib.sha256(settings.ENCRYPTION_KEY.encode()).digest()
    aesgcm = AESGCM(key)
    try:
        data = base64.b64decode(encrypted_value.encode('utf-8'))
        nonce = data[:12]
        ciphertext = data[12:]
        return aesgcm.decrypt(nonce, ciphertext, None).decode('utf-8')
    except Exception as e:
        logger.critical(f"DECRYPTION_FAILURE: Standalone decrypt failed - {e}")
        raise DecryptionError("Failed to decrypt field value.") from e
