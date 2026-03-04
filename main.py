import uvicorn
from sqlalchemy import text
from fastapi import FastAPI
from src.core.config import settings
from src.core.database import engine, Base
from src.routes.ingest_route import router

def init_db():
    try:
        with engine.connect() as connection:
            # 1. Enable the vector extension
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            connection.commit()
            Base.metadata.create_all(bind=engine)
            print("Database tables created successfully.")
    except Exception as e:
        print(f"Database setup failed: {e}")
        raise e

init_db()


app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(router, tags=["Ingestion"])

@app.get("/")
def health_check():
    return {"status": "ok"}

