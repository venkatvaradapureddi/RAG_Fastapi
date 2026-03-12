from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv() 

class Settings(BaseSettings):
    PROJECT_NAME: str = "Book RAG Service"    
    DATABASE_URL: str
    GOOGLE_API_KEY: str
    GCS_BUCKET_NAME: str
    GOOGLE_CLOUD_PROJECT: str
    GOOGLE_CLOUD_LOCATION : str
    #GOOGLE_GENAI_USE_VERTEXAI :  bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()