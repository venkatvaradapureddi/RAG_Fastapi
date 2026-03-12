import io
import uuid
import json
import re
from urllib.parse import quote
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import asyncio
from google.cloud import storage
from src.core.database import get_db
from src.services.retriever import search_books_tool, load_titles
from src.agents.book_agent import book_assistant_agent

from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

router = APIRouter()

class SearchRequest(BaseModel):
    query: str

class SearchResponse(BaseModel):
    answer: str
    session_id: str
    images: list[str]
    tables: list[str]

@router.on_event("startup")
async def startup_event():
    load_titles()
    
session_service = InMemorySessionService()

def is_book_query(query: str) -> bool:
    greetings = ["hi", "hello", "hey", "good morning", "good evening"]
    q = query.lower().strip()
    if q in greetings:
        return False
    return True



def gcs_to_proxy_url(gcs_uri: str) -> str:
    """Convert a gs:// URI to a local proxy URL."""
    return f"/image?gcs_uri={quote(gcs_uri)}"


@router.get("/image")   
async def serve_image(gcs_uri: str = Query(..., description="GCS URI like gs://bucket/path")):
    """Proxy endpoint that downloads an image from GCS and serves it directly."""
    try:
        parts = gcs_uri.replace("gs://", "").split("/", 1)
        bucket_name, blob_path = parts[0], parts[1]

        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_path)

        image_bytes = await asyncio.to_thread(blob.download_as_bytes)

        ext = blob_path.rsplit(".", 1)[-1].lower()
        content_type = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "gif": "image/gif", "webp": "image/webp"}.get(ext, "image/jpeg")

        return StreamingResponse(io.BytesIO(image_bytes), media_type=content_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load image: {e}")


def parse_agent_json(raw_text: str) -> dict:
    """
    Parse the agent's structured JSON response with show_image/show_table flags.
    Handles cases where the JSON might be wrapped in ```json ... ``` code blocks.
    Falls back gracefully if parsing fails.
    """
    code_block_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?\s*```', raw_text, re.DOTALL)
    if code_block_match:
        json_str = code_block_match.group(1).strip()
    else:
        json_str = raw_text.strip()

    try:
        parsed = json.loads(json_str)
        return {
            "answer": parsed.get("answer", raw_text),
            "show_image": parsed.get("show_image", False),
            "show_table": parsed.get("show_table", False),
        }
    except (json.JSONDecodeError, TypeError):
        # if agent didn't return valid JSON, return raw text with no flags
        return {
            "answer": raw_text,
            "show_image": False,
            "show_table": False,
        }


@router.post("/search", response_model=SearchResponse)
async def search_books_endpoint(payload: SearchRequest, db: Session = Depends(get_db)):
    query = payload.query
    images = []
    context = ""
    tables = []

    if is_book_query(query):
        print(f"Searching DB for: {query}")
        try:
            # Pass chat history for context-aware search
            retrieval = await asyncio.to_thread(
                search_books_tool, 
                query
            )
            
            # ensure retrieval is a dictionary and has data
            if isinstance(retrieval, dict):
                context = retrieval.get("context", "")
                images = retrieval.get("images", [])
                tables = retrieval.get("tables", [])
            elif isinstance(retrieval, str):
                print(f"Tool returned string: {retrieval}")
            
        except Exception as e:
            print(f" Tool Error: {e}")
            pass

    
    prompt = f"""
    User Question: {query}

    Database Context:
    {context}

    Respond ONLY in the JSON format specified in your instructions.
    """

    msg = types.Content(role="user", parts=[types.Part(text=prompt)])

    runner = Runner(
        agent=book_assistant_agent,
        session_service=session_service,
        app_name="rag_agent",
    )

    session_id = str(uuid.uuid4())
    user_id = "default_user"


    await session_service.create_session(
        app_name="rag_agent",
        session_id=session_id,
        user_id=user_id
    )
  

    full_response_text = ""

    try:
        async for event in runner.run_async(
            new_message=msg,
            session_id=session_id,
            user_id=user_id
        ):
            
            # Direct Text (Most common in newer SDKs)
            if hasattr(event, "text") and event.text:
                full_response_text += event.text
            
            # Candidates (Standard Gemini Response)
            elif hasattr(event, "candidates") and event.candidates:
                for candidate in event.candidates:
                    if hasattr(candidate, "content") and candidate.content:
                        for part in candidate.content.parts:
                            if hasattr(part, "text") and part.text:
                                full_response_text += part.text

            # Direct Content Parts (Older ADK/specific wrappers)
            elif hasattr(event, "content") and event.content:
                 if hasattr(event.content, "parts"):
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            full_response_text += part.text

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # FALLBACK RESPONSE
    if not full_response_text.strip():
         print("Error: No text extracted from event stream.")
         full_response_text = '{"answer": "I\'m sorry, I\'m having trouble processing that right now.", "show_image": false, "show_table": false}'

    print(full_response_text)
    parsed = parse_agent_json(full_response_text)

    # Use the agent's flags to decide what to include from the DB data
    response_images = [gcs_to_proxy_url(uri) for uri in images] if parsed["show_image"] else []
    response_tables = tables if parsed["show_table"] else []

    return SearchResponse(
        answer=parsed["answer"],
        session_id=session_id,
        images=response_images,
        tables=response_tables
    )