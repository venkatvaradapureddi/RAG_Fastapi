from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv() 

class Settings(BaseSettings):
    PROJECT_NAME: str = "Book RAG Service"    
    DATABASE_URL: str
    GOOGLE_API_KEY: str
    GCS_BUCKET_NAME: str
    # GOOGLE_APPLICATION_CREDENTIALS: str
    GOOGLE_PROJECT_ID: str

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()