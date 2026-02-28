param(
  [Parameter(Mandatory=$true)][string]$PublicUrl
)

$ErrorActionPreference = "Stop"
$PublicUrl = $PublicUrl.Trim()
if (-not $PublicUrl.StartsWith("https://")) { throw "PublicUrl must start with https:// (got: $PublicUrl)" }

$WEBHOOK = ($PublicUrl.TrimEnd("/") + "/tg/webhook")

# update .env WEBHOOK_URL
$envPath = ".env"
$content = Get-Content $envPath -Raw
if ($content -match "(?m)^WEBHOOK_URL=") {
  $content = $content -replace "(?m)^WEBHOOK_URL=.*$", "WEBHOOK_URL=$WEBHOOK"
} else {
  $content = $content.TrimEnd() + "
WEBHOOK_URL=$WEBHOOK
"
}
Set-Content -Path $envPath -Value $content -Encoding UTF8

$TOKEN = (Select-String -Path .env -Pattern "^TELEGRAM_TOKEN=").Line.Split("=",2)[1].Trim()

$secretLine = (Select-String -Path .env -Pattern "^WEBHOOK_SECRET=").Line
$SECRET = ""
if ($secretLine) { $SECRET = $secretLine.Split("=",2)[1].Trim() }

Write-Host "WEBHOOK_URL = $WEBHOOK"
if ($SECRET) { Write-Host "WEBHOOK_SECRET = SET" } else { Write-Host "WEBHOOK_SECRET = MISSING (allowed)" }

$setUrl = "https://api.telegram.org/bot$TOKEN/setWebhook?url=$WEBHOOK&drop_pending_updates=true"
if ($SECRET) { $setUrl = $setUrl + "&secret_token=$SECRET" }

curl.exe -sS "$setUrl" | Out-Host
"
---"
curl.exe -sS "https://api.telegram.org/bot$TOKEN/getWebhookInfo" | Out-Host
