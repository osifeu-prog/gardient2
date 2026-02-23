# --- Setup and Run Telegram Guardian Bot ---

# ודא שאתה בתיקיית הפרויקט
$projectDir = "D:\telegram-guardian-DOCKER-COMPOSE-ENTERPRISE\bot"
cd $projectDir

# בדוק אם ה-venv פעיל
if (-not $env:VIRTUAL_ENV) {
    Write-Host "Virtual environment לא פעיל. מנסה להפעיל .venv..."
    & "$projectDir\.venv\Scripts\Activate.ps1"
}

# עדכון pip
Write-Host "Updating pip..."
python -m pip install --upgrade pip

# התקנת חבילות חובה
Write-Host "Installing required packages..."
pip install --upgrade python-dotenv
pip install --upgrade python-telegram-bot==13.15

# בדיקה אם מודול מובנה קיים (imghdr)
try {
    python -c "import imghdr"
    Write-Host "imghdr נמצא ✅"
} catch {
    Write-Host "imghdr חסר ❌ – כנראה שה‑Python שלך לא התקין stdlib שלם. צריך להתקין Python מחדש או להשתמש ב-Python 3.12"
    exit 1
}

# בדיקה אם .env קיים
if (-not (Test-Path "$projectDir\.env")) {
    Write-Host ".env לא נמצא ❌ – צור קובץ עם BOT_TOKEN"
    exit 1
}

# הפעלת הבוט
Write-Host "Running Telegram Guardian Bot..."
python main.py