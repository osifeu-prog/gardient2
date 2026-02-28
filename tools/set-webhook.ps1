param(
  [Parameter(Mandatory=$true)][string]$PublicUrl
)

$ErrorActionPreference = "Stop"
$PublicUrl = $PublicUrl.Trim()
if (-not $PublicUrl.StartsWith("https://")) { throw "PublicUrl must start with https:// (got: $PublicUrl)" }

$envPath = ".env"
if (-not (Test-Path $envPath)) { throw ".env not found. Create it from .env.template first." }

# Read env
$envRaw = Get-Content $envPath -Raw
$tokenLine = (Select-String -Path $envPath -Pattern "^TELEGRAM_TOKEN=").Line
if (-not $tokenLine) { throw "TELEGRAM_TOKEN missing in .env" }
$TOKEN = $tokenLine.Split("=",2)[1].Trim()
if (-not $TOKEN) { throw "TELEGRAM_TOKEN is empty" }

$secretLine = (Select-String -Path $envPath -Pattern "^WEBHOOK_SECRET=").Line
$SECRET = ""
if ($secretLine) { $SECRET = $secretLine.Split("=",2)[1].Trim() }

$WEBHOOK = ($PublicUrl.TrimEnd("/") + "/tg/webhook")

# Update .env WEBHOOK_URL
if ($envRaw -match "(?m)^WEBHOOK_URL=") {
  $envRaw = $envRaw -replace "(?m)^WEBHOOK_URL=.*$", "WEBHOOK_URL=$WEBHOOK"
} else {
  $envRaw = $envRaw.TrimEnd() + "`nWEBHOOK_URL=$WEBHOOK`n"
}
Set-Content -Path $envPath -Value ($envRaw.Replace("`r`n","`n")) -Encoding UTF8

Write-Host "WEBHOOK_URL = $WEBHOOK"
if ($SECRET) { Write-Host "WEBHOOK_SECRET = SET" } else { Write-Host "WEBHOOK_SECRET = MISSING (allowed)" }

# Build setWebhook URL
$setUrl = "https://api.telegram.org/bot$TOKEN/setWebhook?url=$([uri]::EscapeDataString($WEBHOOK))&drop_pending_updates=true"
if ($SECRET) {
  $setUrl += "&secret_token=$([uri]::EscapeDataString($SECRET))"
}

curl.exe -sS "$setUrl" | Out-Host
"`n---"
curl.exe -sS "https://api.telegram.org/bot$TOKEN/getWebhookInfo" | Out-Host
