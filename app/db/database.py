import os
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

def _to_asyncpg_url(url: str) -> str:
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url

def _to_sync_url(url: str) -> str:
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://", 1)
    return url

def get_async_engine() -> AsyncEngine:
    db = os.getenv("DATABASE_URL", "")
    if not db:
        raise RuntimeError("DATABASE_URL missing")
    return create_async_engine(_to_asyncpg_url(db), echo=False)

def get_sync_engine():
    db = os.getenv("DATABASE_URL", "")
    if not db:
        raise RuntimeError("DATABASE_URL missing")
    return create_engine(_to_sync_url(db), future=True)

def get_sync_sessionmaker():
    eng = get_sync_engine()
    return sessionmaker(bind=eng, autoflush=False, autocommit=False, future=True)