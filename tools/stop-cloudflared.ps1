param(
  [string]$PidFile = ".\_diag\cloudflared.pid"
)

$ErrorActionPreference = "SilentlyContinue"

if (Test-Path $PidFile) {
  $pid = (Get-Content $PidFile -Raw).Trim()
  if ($pid -match "^\d+$") {
    try {
      Stop-Process -Id ([int]$pid) -Force
      Write-Host "Stopped cloudflared pid=$pid" -ForegroundColor Green
      Remove-Item $PidFile -Force
      exit 0
    } catch {}
  }
}

# fallback: stop any cloudflared tunnel processes (best effort)
Get-Process cloudflared -ErrorAction SilentlyContinue | ForEach-Object {
  try { Stop-Process -Id $_.Id -Force } catch {}
}
Write-Host "Stopped cloudflared (best effort)." -ForegroundColor Yellow
