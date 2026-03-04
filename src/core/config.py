from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Book RAG Service"
    API_V1_STR: str = "/api/v1"
    
    # Infrastructure
    DATABASE_URL: str
    GOOGLE_API_KEY: str
    GCS_BUCKET_NAME: str
    GOOGLE_APPLICATION_CREDENTIALS: str

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()