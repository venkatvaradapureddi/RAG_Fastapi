import google.generativeai as genai
from src.core.config import settings

# Initialize once
genai.configure(api_key=settings.GOOGLE_API_KEY)

def generate_embedding(text: str) -> list[float]:
    """
    Generates a 768-dimensional vector using Google's text-embedding-004.
    Used for both Ingestion (now) and Retrieval (future).
    """
    try:
        result = genai.embed_content(
            model="gemini-embedding-001",
            content=text,
            task_type="retrieval_document",
            title="Book Data",
            output_dimensionality=768
        )
        return result['embedding']
    except Exception as e:
        print(f"Embedding Generation Error: {e}")
        raise e