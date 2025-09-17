from sqlalchemy import create_engine

from app.core.config import settings

# Convert your DATABASE_URL to asyncpg format if needed
database_url = settings.DATABASE_URL

engine = create_engine(database_url, pool_size=10, max_overflow=20)
