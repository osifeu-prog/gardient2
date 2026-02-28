param([int]$Port = 8001)
Write-Host "Cloudflare Quick Tunnel -> http://localhost:$Port" -ForegroundColor Cyan
Write-Host "Leave this window OPEN. Copy the https://....trycloudflare.com URL." -ForegroundColor Yellow
cloudflared tunnel --url "http://localhost:$Port"
