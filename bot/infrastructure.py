import os
import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import redis.asyncio as redis

# Configure logger
logger = logging.getLogger("guardian_infra")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

# Environment
DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")

# Global clients
engine = None
redis_client = None

async def init_infrastructure():
    global engine, redis_client

    # Validate environment
    if not DATABASE_URL:
        logger.error("DATABASE_URL missing")
        raise RuntimeError("Infrastructure not configured")
    if not REDIS_URL:
        logger.error("REDIS_URL missing")
        raise RuntimeError("Infrastructure not configured")

    # Convert Railway URL to asyncpg
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL_ASYNC = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://")
    else:
        DATABASE_URL_ASYNC = DATABASE_URL

    # Create DB engine
    engine = create_async_engine(DATABASE_URL_ASYNC, echo=False)

    # Create Redis client
    redis_client = redis.from_url(REDIS_URL)

    # Run healthcheck
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
            raise RuntimeError("PostgreSQL healthcheck failed")

    # Redis check
    pong = await redis_client.ping()
    if pong:
        logger.info("Redis connection: OK")
    else:
        raise RuntimeError("Redis healthcheck failed")