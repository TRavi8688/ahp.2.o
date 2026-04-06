import os
import httpx
import mimetypes
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the same directory as this file
_env_path = Path(__file__).parent / ".env"
load_dotenv(_env_path, override=True)

from app.core.config import settings

INSFORGE_URL = settings.INSFORGE_BASE_URL
INSFORGE_KEY = settings.INSFORGE_ANON_KEY
BUCKET_NAME = settings.S3_BUCKET_NAME

async def upload_to_s3_async(file_path: str, object_name: str) -> str:
    """
    Async upload to InsForge Storage (AWS S3 Replacement).
    Essential for C1K concurrency to prevent event-loop blocking.
    """
    if os.getenv("DEMO_MODE", "False") == "True":
        return f"local://{object_name}"

    if not INSFORGE_KEY:
        return f"local://{object_name}"

    try:
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "application/octet-stream"

        # Build the upload URL
        encoded_key = object_name.replace(" ", "%20")
        url = f"{INSFORGE_URL}/api/storage/buckets/{BUCKET_NAME}/objects/{encoded_key}"

        # Non-blocking file read
        import asyncio
        file_bytes = await asyncio.to_thread(lambda: open(file_path, "rb").read())

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.put(
                url,
                headers={"Authorization": f"Bearer {INSFORGE_KEY}"},
                files={"file": (os.path.basename(file_path), file_bytes, mime_type)}
            )

        if resp.status_code in (200, 201):
            try:
                data = resp.json()
                rel_url = data.get("url", "")
            except:
                rel_url = ""

            if rel_url:
                if rel_url.startswith("/"):
                    rel_url = INSFORGE_URL.rstrip("/") + rel_url
                return rel_url
            else:
                return f"{INSFORGE_URL}/api/storage/buckets/{BUCKET_NAME}/objects/{encoded_key}"
        else:
            return f"local://{object_name}"

    except Exception:
        return f"local://{object_name}"
