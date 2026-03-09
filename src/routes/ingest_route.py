import asyncio
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.core.database import get_db
from src.models.book import Book
from src.services.scraper import scrape_book_details
from src.services.storage import upload_image_to_gcs
from src.services.embedder import generate_embedding

router = APIRouter()
class IngestRequest(BaseModel):
    url: str

class IngestResponse(BaseModel):
    status: str
    book_title: str
    gcs_uri: str | None


@router.post("/ingest", response_model=IngestResponse)
async def ingest_book(payload: IngestRequest, db: Session = Depends(get_db)):
    """
    Ingests a book URL: Scrapes -> Uploads Image -> Embeds -> Saves to DB.
    """
    
    # Scrape (Async I/O)
    data = await scrape_book_details(payload.url)
    
    loop = asyncio.get_event_loop()
    
    # gcs_task = loop.run_in_executor(None, upload_image_to_gcs, data['image_url'])
    # embed_task = loop.run_in_executor(None, generate_embedding, data['content_chunk'])
    
    # gcs_uri, vector = await asyncio.gather(gcs_task, embed_task)
    gcs_uri = None
    vector = await loop.run_in_executor(None, generate_embedding, data['content_chunk'])

    try:
        # Check for existing book to avoid duplicates
        existing_book = db.query(Book).filter(Book.source_url == payload.url).first()
        
        if existing_book:
            existing_book.title = data['title']
            existing_book.content_chunk = data['content_chunk']
            existing_book.image_uri = gcs_uri
            existing_book.product_table = data['product_table']
            existing_book.embedding = vector
        else:
            new_book = Book(
                source_url=payload.url,
                title=data['title'],
                content_chunk=data['content_chunk'],
                product_table=data['product_table'],
                image_uri=gcs_uri,
                embedding=vector
            )
            db.add(new_book)
        
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database commit failed: {str(e)}")

    return IngestResponse(
        status="success",
        book_title=data['title'],
        gcs_uri=gcs_uri
    )