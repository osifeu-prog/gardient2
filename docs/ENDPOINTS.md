# Endpoints & Commands

## HTTP Endpoints (FastAPI)
- GET /healthz
- GET /version
- GET /readyz
- GET /metrics
- POST /tg/webhook

Notes:
- GET /tg/webhook returns 405 (expected). Telegram uses POST.

## Bot Commands (Telegram)
- /start
- /menu
- /status
- /whoami
- /health
- /admin (admin only)
- /vars (admin only)
- /webhook (admin only)
- /diag (admin only)
- /pingdb (admin only)
- /pingredis (admin only)
