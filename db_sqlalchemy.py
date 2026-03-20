from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base


import os
from dotenv import load_dotenv
load_dotenv()


# Prefer local SQLite DATABASE_URL if set, else use Supabase Postgres, else fallback
# Try to build a valid SQLAlchemy Postgres URL from available env vars if needed

def get_postgres_sqlalchemy_url():
    # Try POSTGRES_URL_NON_POOLING first, then POSTGRES_URL, then POSTGRES_PRISMA_URL
    url = os.getenv("DATABASE_URL") 
    if url:
        # Convert to SQLAlchemy format if needed
        if url.startswith("postgres://"):
            # SQLAlchemy expects postgresql+psycopg2://
            url = url.replace("postgres://", "postgresql+psycopg2://", 1)
        return url
    return None

DATABASE_URL = (
    os.getenv("DATABASE_URL")
)


print(f"Using DATABASE_URL: {DATABASE_URL}")  # Debugging line to check which DB URL is being used
# Create the SQLAlchemy engine
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
elif DATABASE_URL.startswith("postgresql"):
    engine = create_engine(DATABASE_URL)
else:
    raise ValueError(f"Invalid or unsupported DATABASE_URL: {DATABASE_URL}")

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables (if they don't exist)
def init_db():
    Base.metadata.create_all(bind=engine)

# Dependency for FastAPI or other usage
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Automatically create tables at import/startup
init_db()
