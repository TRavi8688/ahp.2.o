import boto3
import mimetypes
from botocore.exceptions import ClientError
from app.core.config import settings
from app.core.logging import logger
from typing import Optional

class StorageService:
    """
    ENTERPRISE SECURE STORAGE: S3 implementation with Zero-Trust enforcement.
    1. Objects are private by default.
    2. Access is ONLY granted via short-lived pre-signed URLs.
    3. No public URL leakage.
    """
    def __init__(self):
        self.bucket = settings.S3_BUCKET_NAME
        # AWS credentials must be injected via IAM role or Environment
        # No hardcoded keys allowed.
        self.client = boto3.client('s3')

    async def upload_bytes(self, content: bytes, object_name: str, mime_type: str = "application/octet-stream") -> str:
        """
        Uploads bytes to private storage. 
        Returns the OBJECT NAME (Key), NOT a public URL.
        """
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=object_name,
                Body=content,
                ContentType=mime_type,
                ServerSideEncryption='aws:kms' # Enforce SSE-KMS
            )
            # We return the object name. The caller must use get_signed_url to access it.
            return object_name
        except ClientError as e:
            logger.error("STORAGE_UPLOAD_FAILURE", error=str(e))
            raise RuntimeError(f"Cloud storage upload failed: {e}")

    def get_signed_url(self, object_name: str, expires_in: int = 300) -> str:
        """
        Generates a short-lived pre-signed URL for secure access.
        Default expiry: 5 minutes.
        """
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': object_name},
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            logger.error("PRESIGNED_URL_GENERATION_FAILURE", error=str(e))
            raise RuntimeError(f"Failed to generate secure access link: {e}")

async def upload_bytes_async(content: bytes, object_name: str, mime_type: str = "application/octet-stream") -> str:
    service = StorageService()
    return await service.upload_bytes(content, object_name, mime_type)

async def get_secure_url(object_name: str, expires_in: int = 300) -> str:
    service = StorageService()
    return service.get_signed_url(object_name, expires_in)

async def upload_to_s3_async(file_path: str, object_name: str) -> str:
    """Secure wrapper for local file uploads."""
    with open(file_path, "rb") as f:
        content = f.read()
    mime_type, _ = mimetypes.guess_type(file_path)
    return await upload_bytes_async(content, object_name, mime_type or "application/octet-stream")
