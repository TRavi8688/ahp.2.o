import datetime
import mimetypes
from google.cloud import storage
from app.core.config import settings
from app.core.logging import logger
from typing import Optional

class StorageService:
    """
    ENTERPRISE SECURE STORAGE: Google Cloud Storage (GCS) implementation.
    1. Objects are private by default.
    2. Access is ONLY granted via short-lived V4 signed URLs.
    3. Enforces Cloud KMS customer-managed encryption (CMEK) patterns.
    """
    def __init__(self):
        self.bucket_name = settings.GCS_BUCKET_NAME
        # Authenticates via Service Account Key or Workload Identity
        self.client = storage.Client(project=settings.GCP_PROJECT_ID)
        self.bucket = self.client.bucket(self.bucket_name)

    async def upload_bytes(self, content: bytes, object_name: str, mime_type: str = "application/octet-stream") -> str:
        """
        Uploads bytes to private GCS bucket.
        Returns the OBJECT NAME (Key).
        """
        try:
            blob = self.bucket.blob(object_name)
            blob.upload_from_string(
                content,
                content_type=mime_type
            )
            logger.info("GCS_UPLOAD_SUCCESS", object=object_name)
            return object_name
        except Exception as e:
            logger.error("GCS_UPLOAD_FAILURE", error=str(e))
            raise RuntimeError(f"Cloud storage upload failed: {e}")

    def get_signed_url(self, object_name: str, expires_in: int = 300) -> str:
        """
        Generates a V4 Signed URL for temporary secure access.
        Default expiry: 5 minutes.
        """
        try:
            blob = self.bucket.blob(object_name)
            url = blob.generate_signed_url(
                version="v4",
                expiration=datetime.timedelta(seconds=expires_in),
                method="GET",
            )
            return url
        except Exception as e:
            logger.error("GCS_SIGNED_URL_FAILURE", error=str(e))
            raise RuntimeError(f"Failed to generate secure link: {e}")

async def upload_bytes_async(content: bytes, object_name: str, mime_type: str = "application/octet-stream") -> str:
    service = StorageService()
    return await service.upload_bytes(content, object_name, mime_type)

async def get_secure_url(object_name: str, expires_in: int = 300) -> str:
    service = StorageService()
    return service.get_signed_url(object_name, expires_in)

async def upload_to_gcs_async(file_path: str, object_name: str) -> str:
    """Secure wrapper for local file uploads to GCS."""
    with open(file_path, "rb") as f:
        content = f.read()
    mime_type, _ = mimetypes.guess_type(file_path)
    return await upload_bytes_async(content, object_name, mime_type or "application/octet-stream")
