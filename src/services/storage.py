import uuid
import httpx
from io import BytesIO
from google.cloud import storage
from src.core.config import settings

def upload_image_to_gcs(image_url: str) -> str:
    """
    Downloads image from URL and uploads to Google Cloud Storage.
    Returns: The 'gs://' URI for future retrieval.
    """
    if not image_url:
        return None

    try:
        # 1. Download Image (Sync is fine here as it runs in threadpool later)
        with httpx.Client() as client:
            resp = client.get(image_url)
            if resp.status_code != 200:
                print(f"Failed to download image: {resp.status_code}")
                return None
            image_bytes = resp.content
            content_type = resp.headers.get("content-type", "image/jpeg")

        # 2. Upload to GCS
        filename = f"books/{uuid.uuid4()}.jpg"
        
        client = storage.Client()
        bucket = client.bucket(settings.GCS_BUCKET_NAME)
        blob = bucket.blob(filename)
        
        blob.upload_from_file(BytesIO(image_bytes), content_type=content_type)
        
        return f"gs://{settings.GCS_BUCKET_NAME}/{filename}"

    except Exception as e:
        print(f"GCS Upload Error: {e}")
        return None