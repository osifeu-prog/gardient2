$ErrorActionPreference = "Stop"
$files = git diff --cached --name-only --diff-filter=ACMR
$bad = @()

foreach ($p in $files) {
  if (!(Test-Path $p)) { continue }
  if ($p -match "\.(png|jpg|jpeg|gif|webp|pdf|zip|exe|dll|so|bin)$") { continue }

  $bytes = [System.IO.File]::ReadAllBytes($p)
  $hasBom = ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF)
  if ($hasBom) { $bad += "BOM: $p" }

  $txt = [System.Text.Encoding]::UTF8.GetString($bytes)
  if ($txt -match "(?m)^(<<<<<<<|=======|>>>>>>>)(\s|$)") { $bad += "CONFLICT: $p" }
}

if ($bad.Count -gt 0) {
  Write-Host "❌ pre-commit blocked:" -ForegroundColor Red
  $bad | ForEach-Object { Write-Host " - $_" -ForegroundColor Red }
  exit 1
}

exit 0
