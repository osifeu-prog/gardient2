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

def alembic_indicator() -> str:
    mig_dir = os.path.join(os.getcwd(), "migrations")
    ok = os.path.isdir(mig_dir)
    return f"Alembic: {'OK' if ok else 'MISSING'} (migrations folder)"

async def runtime_report(full: bool = False) -> str:
    lines = []
    lines.append("🧾 SLH Guardian — Runtime Report")
    lines.append(f"ENV: {os.getenv('ENV', 'production')}")
    lines.append(f"MODE: {os.getenv('MODE', 'polling')}")
    lines.append("")
    lines.append(f"Postgres: {'OK' if engine is not None else 'NOT INIT'}")
    lines.append(f"Redis: {'OK' if redis_client is not None else 'NOT INIT'}")
    lines.append(alembic_indicator())

    if full:
        lines.append("")
        lines.append("🔐 Vars present:")
        for k in ("BOT_TOKEN","DATABASE_URL","REDIS_URL","ADMIN_CHAT_ID","WEBHOOK_URL"):
            lines.append(f"{k}: {'SET' if os.getenv(k) else 'MISSING'}")

    return "\n".join(lines)


    # used by /readyz for latency measurement
    await _check_postgres()


    # used by /readyz for latency measurement
    await _check_redis()


async def check_postgres():
    # wrapper used by /readyz
    await check_postgres()

async def check_redis():
    # wrapper used by /readyz
    await check_redis()
