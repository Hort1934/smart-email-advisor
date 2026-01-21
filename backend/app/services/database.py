from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, Session
import os
import logging
from dotenv import load_dotenv

from app.models.database import Base

load_dotenv()
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

# Create engines only if database is configured
engine = None
async_engine = None
SessionLocal = None
AsyncSessionLocal = None

# Check if we're using PostgreSQL
if "postgresql" in DATABASE_URL:
    try:
        ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
        engine = create_engine(DATABASE_URL)
        async_engine = create_async_engine(ASYNC_DATABASE_URL)
    except Exception as e:
        logger.warning(f"PostgreSQL not available, falling back to SQLite: {e}")
        DATABASE_URL = "sqlite+aiosqlite:///./test.db"
        async_engine = create_async_engine(DATABASE_URL)
else:
    # SQLite setup
    async_engine = create_async_engine(DATABASE_URL, echo=True)

# Session makers
if async_engine:
    AsyncSessionLocal = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )

async def init_db():
    """Initialize database tables"""
    try:
        if async_engine:
            async with async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database initialized successfully")
        else:
            logger.warning("Database not configured, skipping initialization")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        logger.info("Application will continue without database")

async def get_async_session() -> AsyncSession:
    """Dependency to get async database session"""
    if not AsyncSessionLocal:
        raise Exception("Database not configured")
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

def get_sync_session() -> Session:
    """Dependency to get sync database session"""
    if not SessionLocal:
        raise Exception("Database not configured")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()