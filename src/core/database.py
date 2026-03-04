from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.core.config import settings

# 1. Create Engine
# pool_pre_ping=True checks connections before using them (vital for production)
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# 2. Session Factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Base Class
Base = declarative_base()

# 4. Dependency for API Routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()