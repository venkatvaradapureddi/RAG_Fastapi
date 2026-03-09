from sqlalchemy.orm import Session
from src.models.book import Book
from src.services.embedder import generate_embedding
from src.core.database import SessionLocal

from rapidfuzz import process, fuzz

BOOK_TITLES = []


def load_titles():
    """
    Load all book titles into memory at application startup.
    """
    global BOOK_TITLES
    db = SessionLocal()
    try:
        titles = db.query(Book.title).all()
        BOOK_TITLES = [t[0] for t in titles]
        print(f"Loaded {len(BOOK_TITLES)} book titles into memory.")
    finally:
        db.close()


def detect_titles(query: str, threshold: int = 80):
    """
    Detect book titles inside user query using fuzzy matching.
    Returns list of matched titles.
    """
    matches = process.extract(
        query,
        BOOK_TITLES,
        scorer=fuzz.partial_ratio,
        limit=5
    )

    matched_titles = [match[0] for match in matches if match[1] >= threshold]
    print(matched_titles)

    return matched_titles


def search_books_tool(query: str):
    db = SessionLocal()

    try:
        # FUZZY TITLE MATCH
        titles = detect_titles(query)

        if titles:
            print("Title match detected:", titles)

            results = db.query(Book).filter(Book.title.in_(titles)).all()

        else:
            # FALLBACK → CHUNK EMBEDDING SEARCH
            print("No title match. Using embedding search.")

            query_vector = generate_embedding(query)

            results = db.query(Book).order_by(
                Book.embedding.cosine_distance(query_vector)
            ).limit(3).all()

        if not results:
            return "No matching books found."

        context = []
        images = []
        tables = []

        for doc in results:
            context.append(
                f"TITLE: {doc.title}\nCONTENT: {doc.content_chunk}"
            )

            if doc.image_uri:
                images.append(doc.image_uri)
            if doc.product_table:
                tables.append(doc.product_table)

        return {
            "context": "\n\n---\n\n".join(context),
            "images": images,
            "tables": tables
        }

    finally:
        db.close()