from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from src.core.database import Base

class Book(Base):
    """
    SQLAlchemy model representing a Book.
    Designed for RAG: separates metadata (title, image) from searchable content.
    """
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    source_url = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    image_uri = Column(String)  
    content_chunk = Column(Text, nullable=False)
    embedding = Column(Vector(768))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())