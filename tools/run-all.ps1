param()

$ErrorActionPreference = "Stop"
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$root = (Get-Location).Path
$reportDir = Join-Path $root "_diag"
New-Item -ItemType Directory -Force $reportDir | Out-Null
$report = Join-Path $reportDir "run_all_$ts.txt"

function Log([string]$m) {
  Write-Host $m
  [System.IO.File]::AppendAllText($report, $m + [Environment]::NewLine)
}

Log "PWD = $root"
Log "Time = $([DateTime]::Now.ToString('s'))"
Log ""

Log "[0] Preconditions"
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw "docker not found" }
if (-not (Get-Command cloudflared -ErrorAction SilentlyContinue)) { throw "cloudflared not found" }
Log "OK"
Log ""

Log "[1] Compose up (build)"
docker compose up -d --build | Out-Null
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | ForEach-Object { Log $_ }
Log ""

Log "[2] Wait for HTTP OK (localhost:8001)"
$ok = $false
for ($i=1; $i -le 60; $i++) {
  $st = (docker inspect -f "{{.State.Status}}" guardian-api 2>$null)
  if ($st -ne "running") { Start-Sleep 1; continue }
  try {
    $h = (curl.exe -sS http://localhost:8001/healthz) 2>$null
    $r = (curl.exe -sS http://localhost:8001/readyz) 2>$null
    if ($h -match '"ok"\s*:\s*true' -and $r -match '"ok"\s*:\s*true') {
      Log "HTTP OK (attempt $i/60)"
      Log $h
      Log "---"
      Log $r
      $ok = $true
      break
    }
  } catch {}
  Start-Sleep 1
}
if (-not $ok) {
  Log "HTTP FAILED. guardian-api logs:"
  docker logs guardian-api --tail 250 | ForEach-Object { Log $_ }
  throw "guardian-api not healthy"
}
Log ""

Log "[3] DB/Redis smoke"
docker exec guardian-db psql -U postgres -d guardian -c "select 1;" | ForEach-Object { Log $_ }
docker exec guardian-redis redis-cli ping | ForEach-Object { Log $_ }
Log ""

Log "[4] Start Cloudflare Quick Tunnel + capture URL"
$cfOut = Join-Path $reportDir "cloudflared_$ts.out.log"
$cfErr = Join-Path $reportDir "cloudflared_$ts.err.log"
$pidFile = Join-Path $reportDir "cloudflared.pid"
if (Test-Path $cfOut) { Remove-Item $cfOut -Force }
if (Test-Path $cfErr) { Remove-Item $cfErr -Force }
if (Test-Path $pidFile) { Remove-Item $pidFile -Force }

$p = Start-Process -FilePath "cloudflared" -ArgumentList @("tunnel","--url","http://localhost:8001") -RedirectStandardOutput $cfOut -RedirectStandardError $cfErr -PassThru -WindowStyle Hidden
Set-Content -Path $pidFile -Value ($p.Id.ToString()) -Encoding ASCII | Out-Null

$public = ""
for ($i=1; $i -le 90; $i++) {
  Start-Sleep 1
  $txt = ""
  if (Test-Path $cfOut) { $txt += (Get-Content $cfOut -Raw) + "`n" }
  if (Test-Path $cfErr) { $txt += (Get-Content $cfErr -Raw) + "`n" }
  $m = [regex]::Match($txt, "https://[a-z0-9-]+\.trycloudflare\.com", "IgnoreCase")
  if ($m.Success) { $public = $m.Value; break }
}
if (-not $public) {
  Log "Failed to capture trycloudflare URL."
  Log "cloudflared OUT (tail):"
  if (Test-Path $cfOut) { (Get-Content $cfOut -Tail 200) | ForEach-Object { Log $_ } }
  Log "cloudflared ERR (tail):"
  if (Test-Path $cfErr) { (Get-Content $cfErr -Tail 200) | ForEach-Object { Log $_ } }
  try { Stop-Process -Id $p.Id -Force } catch {}
  throw "cloudflared URL not found"
}

Log "Public URL = $public"
Log ""

Log "[5] Configure Telegram webhook (uses tools\set-webhook.ps1)"
& .\tools\set-webhook.ps1 -PublicUrl $public | ForEach-Object { Log $_ }
Log ""

Log "[6] Tail guardian-api logs (send /start now)"
docker logs guardian-api --tail 200 | ForEach-Object { Log $_ }
Log ""
Log "DONE. Report saved: $report"
Log "cloudflared pid: $($p.Id)  (stop later: .\tools\stop-cloudflared.ps1)"
Log "cloudflared OUT: $cfOut"
Log "cloudflared ERR: $cfErr"
