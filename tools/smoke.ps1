param(
  [string]$PublicUrl = "",
  [int]$HttpRetrySeconds = 40
)

$ErrorActionPreference = "Stop"

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$report = Join-Path (Get-Location) "_diag\smoke_$ts.txt"

function Tee([string]$s) {
  $s | Out-Host
  Add-Content -Path $report -Value $s
}

Tee "PWD = $(Get-Location)"
Tee "Time = $(Get-Date)"

Tee "
[1] Compose up"
docker compose -f docker-compose.yml up -d | Out-Null
Tee "OK"

Tee "
[2] Containers"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | ForEach-Object { Tee $_ }

Tee "
[3] HTTP smoke (localhost:8001) with retry"
$ok = $false
for ($i=1; $i -le $HttpRetrySeconds; $i++) {
  try {
    $h = (curl.exe -sS http://localhost:8001/healthz) 2>$null
    $r = (curl.exe -sS http://localhost:8001/readyz) 2>$null
    if ($h -match '"ok"\s*:\s*true' -and $r -match '"ok"\s*:\s*true') {
      Tee "HTTP OK (attempt $i/$HttpRetrySeconds)"
      Tee $h
      Tee "---"
      Tee $r
      $ok = $true
      break
    }
  } catch {}
  Start-Sleep -Seconds 1
}

if (-not $ok) {
  Tee "HTTP FAILED after retries. guardian-api logs:"
  docker logs guardian-api --tail 200 | ForEach-Object { Tee $_ }
  throw "HTTP smoke failed"
}

Tee "
[4] DB/Redis smoke"
try {
  docker exec guardian-db psql -U postgres -d guardian -c "select 1;" | ForEach-Object { Tee $_ }
  docker exec guardian-redis redis-cli ping | ForEach-Object { Tee $_ }
  Tee "DB/Redis OK"
} catch {
  Tee "DB/Redis FAILED: $_"
  throw
}

if ($PublicUrl) {
  Tee "
[5] Configure Telegram Webhook"
  & .\tools\set-webhook.ps1 -PublicUrl $PublicUrl | Out-Null
  Tee "Webhook configured."

  Tee "
[6] Tail logs (send /start to the bot now)"
  docker logs guardian-api --tail 200 | ForEach-Object { Tee $_ }
} else {
  Tee "
[5] Webhook skipped (no -PublicUrl provided)"
  Tee "Tip: .\tools\smoke.ps1 -PublicUrl https://xxxxx.trycloudflare.com"
}

Tee "
DONE. Report: $report"

exit 0

