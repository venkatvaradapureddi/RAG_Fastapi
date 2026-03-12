import os
import httpx
import asyncio
from io import BytesIO
from google.cloud import storage
from src.core.config import settings
from urllib.parse import urlparse


client = storage.Client(project=settings.GOOGLE_CLOUD_PROJECT)
async def upload_image_to_gcs(image_url: str) -> str | None:
    """
    Downloads image asynchronously and uploads to GCS.
    """

    if not image_url:
        return None

    try:
        async with httpx.AsyncClient(verify=False) as http_client:
            resp = await http_client.get(image_url)

            if resp.status_code != 200:
                print(f"Failed to download image: {resp.status_code}")
                return None

            image_bytes = resp.content
            content_type = resp.headers.get("content-type", "image/jpeg")

        parsed_url = urlparse(image_url)
        original_filename = os.path.basename(parsed_url.path)

        # fallback if filename missing
        if not original_filename:
            original_filename = "image.jpg"

        filename = f"books/{original_filename}"
        def upload():
            bucket = client.bucket(settings.GCS_BUCKET_NAME)
            blob = bucket.blob(filename)

            blob.upload_from_file(BytesIO(image_bytes), content_type=content_type)

            return f"gs://{settings.GCS_BUCKET_NAME}/{filename}"

        return await asyncio.to_thread(upload)

    except Exception as e:
        print(f"GCS Upload Error: {e}")
        return None