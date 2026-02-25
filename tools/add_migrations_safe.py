from pathlib import Path
import re

p = Path("bot/infrastructure.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

# Ensure imports
if "from alembic.config import Config" not in s:
    s = s.replace("import redis.asyncio as redis\n", "import redis.asyncio as redis\nfrom alembic import command\nfrom alembic.config import Config\n")

if "async def run_migrations_safe" not in s:
    s += """

async def run_migrations_safe():
    \"\"\"Run alembic upgrade head safely (do not crash app if it fails).\"\"\"
    if not DATABASE_URL:
        logger.warning("migrations: DATABASE_URL missing; skip")
        return
    try:
        cfg = Config("alembic.ini")
        # Alembic uses sync engine internally; it can work with DATABASE_URL (psycopg2) or asyncpg url depending on config.
        # We keep it simple: rely on existing alembic.ini settings.
        command.upgrade(cfg, "head")
        logger.info("migrations: alembic upgrade head OK")
    except Exception as e:
        logger.error("migrations: alembic upgrade failed: %s: %s", type(e).__name__, e)
"""

p.write_text(s, encoding="utf-8")
print("OK: added run_migrations_safe() to bot/infrastructure.py")
