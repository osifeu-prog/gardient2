# ===============================
# Guardian Enterprise - PowerShell
# ===============================

# נתיב הפרויקט
$ROOT = "D:\telegram-guardian-DOCKER-COMPOSE-ENTERPRISE"
Set-Location $ROOT

# -------------------------------
# יצירת קובץ .env אם לא קיים
# -------------------------------
$envPath = Join-Path $ROOT ".env"
if (-Not (Test-Path $envPath)) {
@"
# -------------------------------
# PostgreSQL Database
# -------------------------------
POSTGRES_DB=guardian
POSTGRES_USER=guardian
POSTGRES_PASSWORD=guardianpass
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

DATABASE_URL=postgresql+psycopg2://guardian:guardianpass@postgres:5432/guardian

# -------------------------------
# Redis
# -------------------------------
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_USER=default
REDIS_PASSWORD=
REDIS_URL=redis://redis:6379/0

# -------------------------------
# Telegram Bot
# -------------------------------
BOT_TOKEN=PUT_YOUR_TOKEN_HERE

# -------------------------------
# Environment
# -------------------------------
ENVIRONMENT=production
"@ | Out-File -Encoding utf8 $envPath
Write-Host "✅ .env נוצר בהצלחה - הכנס את הטוקן שלך במקום PUT_YOUR_TOKEN_HERE"
} else {
    Write-Host "⚠️ .env כבר קיים - בדוק שהטוקן מעודכן"
}

# -------------------------------
# יצירת docker-compose.yml אם לא קיים
# -------------------------------
$dcPath = Join-Path $ROOT "docker-compose.yml"
if (-Not (Test-Path $dcPath)) {
@"
services:

  postgres:
    image: postgres:17
    restart: always
    env_file: .env
    volumes:
      - pg_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:8
    restart: always
    command: ["redis-server", "--loadmodule", "/usr/local/lib/redis/modules/redisbloom.so", "--loadmodule", "/usr/local/lib/redis/modules/redisearch.so", "--loadmodule", "/usr/local/lib/redis/modules/redistimeseries.so", "--loadmodule", "/usr/local/lib/redis/modules/rejson.so"]
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  api:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    depends_on:
      - postgres
      - redis
    env_file: .env
    ports:
      - "8000:8000"

  bot:
    build: .
    command: python services/bot/run_bot.py
    depends_on:
      - postgres
      - redis
    env_file: .env

  worker:
    build: .
    command: celery -A app.core.celery worker --loglevel=info
    depends_on:
      - redis
      - postgres
    env_file: .env

  scheduler:
    build: .
    command: celery -A app.core.celery beat --loglevel=info
    depends_on:
      - redis
      - postgres
    env_file: .env

volumes:
  pg_data:
  redis_data:
"@ | Out-File -Encoding utf8 $dcPath
    Write-Host "✅ docker-compose.yml נוצר בהצלחה"
} else {
    Write-Host "⚠️ docker-compose.yml כבר קיים"
}

# -------------------------------
# הרצת Docker Compose
# -------------------------------
Write-Host "🚀 מתחיל הרצת כל השירותים..."
docker compose up -d

# -------------------------------
# בדיקה בסיסית של חיבורי השירותים
# -------------------------------
Write-Host "`n🔹 בדיקת מצב קונטיינרים..."
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

Write-Host "`n🔹 הצגת לוגים 5 דקות אחרונות לכל השירותים (API, Bot, Worker, Scheduler)..."
docker compose logs --tail=50 api bot worker scheduler
Write-Host "`n✅ אם כל השירותים 'Up', אפשר להתחיל לעבוד עם הבוט"