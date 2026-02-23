import os
import logging
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import redis.asyncio as redis

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")

engine = None
redis_client = None

async def init_infrastructure():
    global engine, redis_client

    if not DATABASE_URL:
        raise ValueError("DATABASE_URL not set")

    if not REDIS_URL:
        raise ValueError("REDIS_URL not set")

    # Convert Railway URL to asyncpg format
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL_ASYNC = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://")
    else:
        DATABASE_URL_ASYNC = DATABASE_URL

    engine = create_async_engine(DATABASE_URL_ASYNC, echo=False)

    redis_client = redis.from_url(REDIS_URL)

    await healthcheck()

async def healthcheck():
    logger.info("Running infrastructure healthcheck...")

    # Postgres check
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT 1"))
        val = result.scalar()
        if val == 1:
            logger.info("PostgreSQL connection: OK")
        else:
            raise Exception("PostgreSQL check failed")

    # Redis check
    pong = await redis_client.ping()
    if pong:
        logger.info("Redis connection: OK")
    else:
        raise Exception("Redis check failed")

    logger.info("Infrastructure ready.")
