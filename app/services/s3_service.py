import os
import requests
import mimetypes
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the same directory as this file — works regardless of cwd
_env_path = Path(__file__).parent / ".env"
load_dotenv(_env_path, override=True)

from app.core.config import settings

INSFORGE_URL = settings.INSFORGE_BASE_URL
INSFORGE_KEY = settings.INSFORGE_ANON_KEY
BUCKET_NAME = settings.S3_BUCKET_NAME

print(f"[s3_service] InsForge URL: {INSFORGE_URL}")
print(f"[s3_service] InsForge KEY loaded: {'YES' if INSFORGE_KEY else 'NO - MISSING!'}")


def upload_to_s3(file_path: str, object_name: str) -> str:
    """
    Uploads a file to InsForge Storage (replaces AWS S3).
    Returns the full public URL of the uploaded file.
    File is stored as: reports/{patient_ahp_id}/{timestamp}.ext
    """
    if not INSFORGE_KEY:
        print("[s3_service] INSFORGE_KEY missing — cannot upload.")
        return f"local://{object_name}"

    try:
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "application/octet-stream"

        # Build the upload URL — InsForge requires multipart/form-data PUT
        encoded_key = object_name.replace(" ", "%20")
        url = f"{INSFORGE_URL}/api/storage/buckets/{BUCKET_NAME}/objects/{encoded_key}"

        print(f"[s3_service] Uploading to: {url}")

        with open(file_path, "rb") as f:
            file_bytes = f.read()

        resp = requests.put(
            url,
            headers={"Authorization": f"Bearer {INSFORGE_KEY}"},
            files={"file": (os.path.basename(file_path), file_bytes, mime_type)},
            timeout=45
        )

        print(f"[s3_service] Response: {resp.status_code} {resp.text[:200]}")

        if resp.status_code in (200, 201):
            try:
                data = resp.json()
                rel_url = data.get("url", "")
            except Exception:
                rel_url = ""

            if rel_url:
                # Build full absolute URL if InsForge returned a relative path
                if rel_url.startswith("/"):
                    rel_url = INSFORGE_URL.rstrip("/") + rel_url
                print(f"[s3_service] Upload SUCCESS: {rel_url}")
                return rel_url
            else:
                # Construct public URL manually for public buckets
                public_url = f"{INSFORGE_URL}/api/storage/buckets/{BUCKET_NAME}/objects/{encoded_key}"
                print(f"[s3_service] Upload SUCCESS (manual URL): {public_url}")
                return public_url
        else:
            print(f"[s3_service] Upload FAILED {resp.status_code}: {resp.text}")
            return f"local://{object_name}"

    except Exception as e:
        print(f"[s3_service] Upload EXCEPTION: {e}")
        return f"local://{object_name}"
