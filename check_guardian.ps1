# check_guardian.ps1
# ------------------
# בדיקה מקיפה של פרויקט Telegram Guardian

# מיקום הפרויקט
$ROOT = Get-Location
Write-Host "`n🧪 Telegram Guardian Project Check - $ROOT`n"

# ------------------
# 1️⃣ בדיקת קובץ .env
$envPath = Join-Path $ROOT ".env"
if (Test-Path $envPath) {
    Write-Host "✅ .env file found"
    Get-Content $envPath | ForEach-Object { Write-Host "   $_" }
} else {
    Write-Host "❌ .env file NOT found!"
}

# ------------------
# 2️⃣ בדיקת docker-compose.yml
$dcPath = Join-Path $ROOT "docker-compose.yml"
if (Test-Path $dcPath) {
    Write-Host "✅ docker-compose.yml found"
} else {
    Write-Host "❌ docker-compose.yml NOT found!"
}

# ------------------
# 3️⃣ בדיקת Docker
Write-Host "`n🔹 Docker version"
docker --version

Write-Host "🔹 Docker Compose version"
docker-compose --version

# ------------------
# 4️⃣ בדיקת containers פעילים
Write-Host "`n🔹 Active Docker containers"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# ------------------
# 5️⃣ בדיקת PostgreSQL connectivity
Write-Host "`n🔹 Testing PostgreSQL connection..."
try {
    $pgUser = "guardian"
    $pgPass = "guardianpass"
    $pgHost = "localhost"
    $pgPort = 5432
    $pgDb = "guardian"
    $conn = "PGPASSWORD=$pgPass psql -h $pgHost -U $pgUser -d $pgDb -c '\l'"
    Invoke-Expression $conn
    Write-Host "✅ PostgreSQL connection OK"
} catch {
    Write-Host "❌ PostgreSQL connection FAILED"
}

# ------------------
# 6️⃣ בדיקת Redis connectivity
Write-Host "`n🔹 Testing Redis connection..."
try {
    $redisHost = "localhost"
    $redisPort = 6379
    $ping = docker run --rm redis:8 redis-cli -h $redisHost -p $redisPort PING
    if ($ping -eq "PONG") {
        Write-Host "✅ Redis connection OK"
    } else {
        Write-Host "❌ Redis connection FAILED"
    }
} catch {
    Write-Host "❌ Redis test FAILED"
}

# ------------------
# 7️⃣ בדיקת Python + FastAPI
Write-Host "`n🔹 Testing FastAPI imports..."
try {
    docker run --rm -v "$ROOT:/app" -w /app python:3.11-slim python -c `
        "import sys; import fastapi; import uvicorn; print('✅ Python + FastAPI imports OK')"
} catch {
    Write-Host "❌ Python/FastAPI import FAILED"
}

# ------------------
# 8️⃣ בדיקת Telegram Bot Token
Write-Host "`n🔹 Testing Telegram Bot token (basic check)"
$botToken = "YOUR_BOT_TOKEN_HERE"
$resp = Invoke-RestMethod -Uri "https://api.telegram.org/bot$botToken/getMe" -Method Get -ErrorAction SilentlyContinue
if ($resp.ok -eq $true) {
    Write-Host "✅ Telegram Bot token OK: $($resp.result.username)"
} else {
    Write-Host "❌ Telegram Bot token INVALID or unreachable"
}

# ------------------
Write-Host "`n🎯 Guardian Project Check Complete`n"