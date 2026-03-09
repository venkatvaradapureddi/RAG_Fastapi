import uuid
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.core.database import get_db
from src.services.retriever import search_books_tool,load_titles
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

@router.post("/search", response_model=SearchResponse)
async def search_books_endpoint(payload: SearchRequest, db: Session = Depends(get_db)):
    query = payload.query
    images = []
    context = ""
    tables = []

    if is_book_query(query):
        print(f"🔎 Searching DB for: {query}")
        try:
            retrieval = search_books_tool(query)
            
            # SAFETY CHECK: Ensure retrieval is a dictionary and has data
            if isinstance(retrieval, dict):
                context = retrieval.get("context", "")
                images = retrieval.get("images", [])
                tables = retrieval.get("tables", [])
            elif isinstance(retrieval, str):
                # Handle case where tool returns a string error message
                print(f"Tool returned string: {retrieval}")
            
        except Exception as e:
            print(f" Tool Error: {e}")
            pass
            
    
    prompt = f"""
    User Question: {query}
    Database Context:
    {context}
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
            
            # EXTRACTION STRATEGY 1: Direct Text (Most common in newer SDKs)
            if hasattr(event, "text") and event.text:
                full_response_text += event.text
            
            # EXTRACTION STRATEGY 2: Candidates (Standard Gemini Response)
            elif hasattr(event, "candidates") and event.candidates:
                for candidate in event.candidates:
                    if hasattr(candidate, "content") and candidate.content:
                        for part in candidate.content.parts:
                            if hasattr(part, "text") and part.text:
                                full_response_text += part.text

            # EXTRACTION STRATEGY 3: Direct Content Parts (Older ADK/specific wrappers)
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
         full_response_text = "I'm sorry, I'm having trouble processing that right now."

    return SearchResponse(
        answer=full_response_text,
        session_id=session_id,
        images=images,
        tables=tables
    )