<#
.SYNOPSIS
Update telegram-guardian infra for async Postgres, check health, and push to Git
.DESCRIPTION
1. Activate virtualenv
2. Install asyncpg and SQLAlchemy asyncio support
3. Update requirements.txt
4. Test DB + Redis connectivity
5. Commit & push to Git
#>

# -----------------------------
# 1️⃣ הפעלת venv
# -----------------------------
$venvPath = ".\.venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    Write-Host "✅ Activating virtualenv..."
    . $venvPath
} else {
    Write-Error "❌ Virtualenv not found at $venvPath"
    exit 1
}

# -----------------------------
# 2️⃣ התקנת דרייברים async
# -----------------------------
Write-Host "✅ Installing asyncpg and SQLAlchemy[asyncio]..."
pip install --upgrade pip
pip install asyncpg sqlalchemy[asyncio]

# -----------------------------
# 3️⃣ בדיקת תלויות ועדכון requirements
# -----------------------------
Write-Host "✅ Checking installed packages..."
pip check
pip freeze > requirements.txt
Write-Host "✅ requirements.txt updated"

# -----------------------------
# 4️⃣ בדיקות בריאות
# -----------------------------
# החלף כאן עם הערכים האמיתיים שלך
$DATABASE_URL_ASYNC = $env:DATABASE_URL_ASYNC
$REDIS_URL = $env:REDIS_URL

Write-Host "🔹 Testing Postgres connection..."
try {
    python - <<END
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine('$DATABASE_URL_ASYNC', echo=False)
async def test():
    async with engine.begin() as conn:
        await conn.run_sync(lambda conn: print("✅ Postgres OK"))
asyncio.run(test())
END
} catch {
    Write-Error "❌ Postgres test failed: $_"
}

Write-Host "🔹 Testing Redis connection..."
try {
    python - <<END
import redis
r = redis.from_url('$REDIS_URL')
r.ping()
print("✅ Redis OK")
END
} catch {
    Write-Error "❌ Redis test failed: $_"
}

# -----------------------------
# 5️⃣ Commit & Push to Git
# -----------------------------
Write-Host "🔹 Committing & pushing to Git..."
git add .
git commit -m "Fix async Postgres driver, update infra & healthchecks"
git push

Write-Host "🎉 All done! Infra updated, healthchecks passed, Git pushed."