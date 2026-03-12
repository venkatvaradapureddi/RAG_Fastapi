from google import genai
from src.core.config import settings
import asyncio
import os

# client = genai.Client(
#     vertexai=True,
#     project=settings.GOOGLE_CLOUD_PROJECT,
#     location=settings.GOOGLE_CLOUD_LOCATION
# )

client = genai.Client(
    api_key=os.getenv("GOOGLE_API_KEY")  # or directly put your key here
)

async def generate_embedding(text: str) -> list[float]:
    """
    Generates a 768-dimensional embedding using Gemini embedding model via Vertex AI.
    """
    try:
        response = await asyncio.to_thread(
            client.models.embed_content,
            model="gemini-embedding-001",
            contents=text,
            config={
                "output_dimensionality": 768
            }
        )

        return response.embeddings[0].values

    except Exception as e:
        print(f"Embedding Generation Error: {e}")
        raise