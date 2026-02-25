from pathlib import Path
import re

p = Path("bot/infrastructure.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

# Ensure imports
if "async_sessionmaker" not in s or "AsyncSession" not in s:
    s = s.replace(
        "from sqlalchemy.ext.asyncio import create_async_engine",
        "from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession"
    )

# Ensure SessionLocal global exists
if re.search(r"(?m)^SessionLocal\s*=\s*None\s*$", s) is None:
    s = re.sub(r"(?m)^engine\s*=\s*None\s*$", "engine = None\nSessionLocal = None", s, count=1)

# In init_infrastructure: make SessionLocal assignment robust (insert after engine creation line)
m = re.search(r"(?m)^\s*engine\s*=\s*create_async_engine\([^\n]*\)\s*$", s)
if not m:
    raise SystemExit("ERROR: cannot find engine=create_async_engine(...) in init_infrastructure")

engine_line = m.group(0)

# Remove any broken/duplicate SessionLocal assignment blocks first (best-effort)
s = re.sub(r"(?s)\n\s*# SQLAlchemy async sessions.*?SessionLocal\s*=.*?\n", "\n", s)

insert = engine_line + "\n    global SessionLocal\n    SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)"
s = s.replace(engine_line, insert, 1)

# Ensure get_db_session exists
if "async def get_db_session" not in s and "def get_db_session" not in s:
    if "from contextlib import asynccontextmanager" not in s:
        s = s.replace("import logging\n", "import logging\nfrom contextlib import asynccontextmanager\n")
    s += """

from contextlib import asynccontextmanager

@asynccontextmanager
async def get_db_session():
    if SessionLocal is None:
        raise RuntimeError("DB session factory not initialized (call init_infrastructure first)")
    async with SessionLocal() as session:
        yield session
"""

p.write_text(s, encoding="utf-8")
print("OK: patched infrastructure SessionLocal + get_db_session")
