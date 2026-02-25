from pathlib import Path
import re

p = Path("bot/infrastructure.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

# 1) Ensure needed imports
if "async_sessionmaker" not in s or "AsyncSession" not in s:
    s = s.replace(
        "from sqlalchemy.ext.asyncio import create_async_engine",
        "from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession"
    )

if "from contextlib import asynccontextmanager" not in s:
    s = s.replace("import logging\n", "import logging\nfrom contextlib import asynccontextmanager\n")

# 2) Add SessionLocal global near engine/redis_client
if re.search(r"(?m)^SessionLocal\s*=\s*None\s*$", s) is None:
    s = re.sub(
        r"(?m)^engine\s*=\s*None\s*$",
        "engine = None\nSessionLocal = None",
        s,
        count=1
    )

# 3) In init_infrastructure: after engine create, set SessionLocal
# find line: engine = create_async_engine(...)
m = re.search(r"(?m)^\s*engine\s*=\s*create_async_engine\([^\n]*\)\s*$", s)
if not m:
    raise SystemExit("ERROR: could not find engine = create_async_engine(...) line")

engine_line = m.group(0)
if "SessionLocal" not in s:
    s = s.replace(
        engine_line,
        engine_line + "\n    # SQLAlchemy async sessions\n    global SessionLocal\n    SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)"
    )

# 4) Add get_db_session if missing
if "def get_db_session" not in s:
    s += """

@asynccontextmanager
async def get_db_session():
    if SessionLocal is None:
        raise RuntimeError("DB session factory not initialized (call init_infrastructure first)")
    async with SessionLocal() as session:
        yield session
"""

p.write_text(s, encoding="utf-8")
print("OK: patched bot/infrastructure.py (added SessionLocal + get_db_session)")
