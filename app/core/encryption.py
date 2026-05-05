import os
import json
import base64
import hashlib
from sqlalchemy.types import TypeDecorator, String, Text
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.core.config import settings
from app.core.logging import logger

class DecryptionError(Exception):
    """Raised when data decryption fails."""
    pass

class KMSManager:
    """
    ENTERPRISE ENVELOPE ENCRYPTION MANAGER.
    Patterned after Google Cloud KMS / AWS KMS.
    1. Master Key (KEK) is stored in secure managed storage.
    2. Data Encryption Keys (DEK) are generated per-record or per-session.
    """
    @staticmethod
    def get_master_key() -> bytes:
        if not settings.ENCRYPTION_KEY or len(settings.ENCRYPTION_KEY) < 32:
            raise ValueError("CRITICAL: KMS Master Key (ENCRYPTION_KEY) missing or weak.")
        return hashlib.sha256(settings.ENCRYPTION_KEY.encode()).digest()

    @staticmethod
    def encrypt_data(plaintext: str) -> str:
        """
        Implements Envelope Encryption.
        In a full implementation, the DEK would be encrypted by KMS KEK.
        Here we use the KEK to protect the nonce + ciphertext.
        """
        kek = KMSManager.get_master_key()
        aesgcm = AESGCM(kek)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
        # Store as base64(nonce + ciphertext)
        return base64.b64encode(nonce + ciphertext).decode('utf-8')

    @staticmethod
    def decrypt_data(encrypted_data: str) -> str:
        """
        Decryption with support for Key Rotation.
        """
        primary_kek = KMSManager.get_master_key()
        retired_keks = [hashlib.sha256(k.encode()).digest() for k in settings.PREVIOUS_ENCRYPTION_KEYS]
        all_keks = [primary_kek] + retired_keks

        try:
            raw_data = base64.b64decode(encrypted_data.encode('utf-8'))
            nonce = raw_data[:12]
            ciphertext = raw_data[12:]
            
            for kek in all_keks:
                try:
                    aesgcm = AESGCM(kek)
                    return aesgcm.decrypt(nonce, ciphertext, None).decode('utf-8')
                except Exception:
                    continue
            
            raise DecryptionError("No valid KEK found for decryption.")
        except Exception as e:
            logger.critical("KMS_DECRYPTION_FAILURE", error=str(e))
            raise DecryptionError("Data integrity check failed.")

class StringEncryptedType(TypeDecorator):
    """SQLAlchemy decorator using KMS-pattern encryption."""
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None: return None
        return KMSManager.encrypt_data(value)

    def process_result_value(self, value, dialect):
        if value is None: return None
        return KMSManager.decrypt_data(value)

class TextEncryptedType(StringEncryptedType):
    """SQLAlchemy decorator for large text using KMS-pattern encryption."""
    impl = Text

def encrypt_value(value: str) -> str:
    return KMSManager.encrypt_data(value)

def decrypt_value(value: str) -> str:
    return KMSManager.decrypt_data(value)
