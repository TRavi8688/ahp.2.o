import boto3
import mimetypes
from botocore.exceptions import ClientError
from app.core.config import settings
from app.core.logging import logger

class StorageService:
    """
    ENTERPRISE CLOUD STORAGE: Generic S3-Compatible implementation.
    Decoupled from specific cloud backbones.
    """
    def __init__(self):
        self.bucket = settings.S3_BUCKET_NAME
        # AWS_ACCESS_KEY_ID etc should be in env
        self.client = boto3.client('s3') 

    async def upload_bytes(self, content: bytes, object_name: str, mime_type: str = "application/octet-stream") -> str:
        """Uploads raw bytes to secure storage."""
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=object_name,
                Body=content,
                ContentType=mime_type
            )
            return f"https://{self.bucket}.s3.amazonaws.com/{object_name}"
        except ClientError as e:
            logger.error("STORAGE_UPLOAD_FAILURE", error=str(e))
            raise RuntimeError(f"Cloud storage upload failed: {e}")

async def upload_bytes_async(content: bytes, object_name: str, mime_type: str = "application/octet-stream") -> str:
    service = StorageService()
    return await service.upload_bytes(content, object_name, mime_type)

async def upload_to_s3_async(file_path: str, object_name: str) -> str:
    """Legacy wrapper."""
    with open(file_path, "rb") as f:
        content = f.read()
    mime_type, _ = mimetypes.guess_type(file_path)
    return await upload_bytes_async(content, object_name, mime_type or "application/octet-stream")
