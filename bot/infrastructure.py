import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import redis.asyncio as redis

logger = logging.getLogger("guardian_infra")

DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")

engine = None
redis_client = None

def _to_asyncpg_url(url: str) -> str:
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url

async def init_infrastructure():
    global engine, redis_client

    if not DATABASE_URL:
        logger.error("DATABASE_URL missing")
        raise RuntimeError("Infrastructure not configured")
    if not REDIS_URL:
        logger.error("REDIS_URL missing")
        raise RuntimeError("Infrastructure not configured")

    db_url_async = _to_asyncpg_url(DATABASE_URL)

    engine = create_async_engine(db_url_async, echo=False)
    redis_client = redis.from_url(REDIS_URL)

    await healthcheck()

async def healthcheck():
    logger.info("Running infrastructure healthcheck...")

    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT 1"))
        if result.scalar() == 1:
            logger.info("PostgreSQL connection: OK")
        else:
            raise RuntimeError("PostgreSQL healthcheck failed")

    if await redis_client.ping():
        logger.info("Redis connection: OK")
    else:
        raise RuntimeError("Redis healthcheck failed")
