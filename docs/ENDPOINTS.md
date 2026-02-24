# Endpoints & Bot Commands

## HTTP Endpoints (FastAPI)
- GET /healthz
- GET /version
- GET /readyz
- GET /metrics
- POST /tg/webhook

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

Notes:
- /tg/webhook returns 405 for GET (expected). Telegram uses POST.

