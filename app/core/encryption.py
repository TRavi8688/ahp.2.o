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
        """Lazy loader for AES-GCM engine with standardized key derivation."""
        if not settings.ENCRYPTION_KEY or len(settings.ENCRYPTION_KEY) < 32:
             logger.critical("MISSING_ENCRYPTION_KEY: AES-GCM requires a 32-character key.")
             raise ValueError("CRITICAL: ENCRYPTION_KEY not found or too short (min 32 chars).")
        
        try:
             # Always derive a 32-byte key from the secret for consistency
             key = hashlib.sha256(settings.ENCRYPTION_KEY.encode()).digest()
             return AESGCM(key)
        except Exception as e:
             logger.critical(f"ENCRYPTION_KEY_INIT_ERROR: {e}")
             raise ValueError(f"CRITICAL: Could not initialize AES-GCM engine: {e}")

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
        
        # 1. Prepare keys (Primary + Retired)
        # Standardize key derivation: always use SHA256 of the provided secret for consistency
        primary_key = hashlib.sha256(settings.ENCRYPTION_KEY.encode()).digest()
        retired_keys = []
        if hasattr(settings, "PREVIOUS_ENCRYPTION_KEYS") and settings.PREVIOUS_ENCRYPTION_KEYS:
            retired_keys = [hashlib.sha256(k.encode()).digest() for k in settings.PREVIOUS_ENCRYPTION_KEYS]
        
        all_keys = [primary_key] + retired_keys
        
        try:
            data = base64.b64decode(value.encode('utf-8'))
            nonce = data[:12]
            ciphertext = data[12:]
            
            # Try all keys in sequence
            for k in all_keys:
                try:
                    aesgcm = AESGCM(k)
                    return aesgcm.decrypt(nonce, ciphertext, None).decode('utf-8')
                except Exception:
                    continue
            
            logger.critical("DECRYPTION_FAILURE: No valid key found for data.")
            raise DecryptionError("Data integrity check failed: No valid encryption key found.")
        except DecryptionError:
            raise
        except Exception as e:
            logger.error(f"DECRYPTION_CRASH: {e}")
            raise DecryptionError(f"Encryption subsystem failure: {str(e)}")

class TextEncryptedType(StringEncryptedType):
    """AES-GCM encryption for SQLAlchemy Text fields (unlimited length)."""
    impl = Text

def encrypt_value(value: str) -> str:
    """Standalone AES-GCM encryption helper."""
    if not value: return ""
    key = hashlib.sha256(settings.ENCRYPTION_KEY.encode()).digest()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, value.encode('utf-8'), None)
    return base64.b64encode(nonce + ciphertext).decode('utf-8')

def decrypt_value(encrypted_value: str) -> str:
    """Standalone AES-GCM decryption helper with rotation support."""
    if not encrypted_value: return ""
    
    primary_key = hashlib.sha256(settings.ENCRYPTION_KEY.encode()).digest()
    retired_keys = []
    if hasattr(settings, "PREVIOUS_ENCRYPTION_KEYS") and settings.PREVIOUS_ENCRYPTION_KEYS:
        retired_keys = [hashlib.sha256(k.encode()).digest() for k in settings.PREVIOUS_ENCRYPTION_KEYS]
    
    all_keys = [primary_key] + retired_keys
    
    try:
        data = base64.b64decode(encrypted_value.encode('utf-8'))
        nonce = data[:12]
        ciphertext = data[12:]
        
        for k in all_keys:
            try:
                aesgcm = AESGCM(k)
                return aesgcm.decrypt(nonce, ciphertext, None).decode('utf-8')
            except Exception:
                continue
        
        raise DecryptionError("No valid encryption key found for the data.")
    except Exception as e:
        logger.critical(f"DECRYPTION_FAILURE: Standalone decrypt failed - {e}")
        raise DecryptionError("Failed to decrypt field value.") from e
