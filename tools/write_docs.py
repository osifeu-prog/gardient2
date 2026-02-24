from pathlib import Path

docs = {
"docs/RUNBOOK.md": """# SLH Guardian (gardient2) ? RUNBOOK

## Production
- Domain: https://gardient2-production.up.railway.app
- Webhook: https://gardient2-production.up.railway.app/tg/webhook
- Mode: webhook-only (Telegram -> POST /tg/webhook)

## Quick checks
- GET /healthz  -> ok + uptime_s + git_sha
- GET /version  -> service + git_sha + uptime_s
- GET /readyz   -> ok + elapsed_ms
- GET /metrics  -> Prometheus metrics text
- Bot: /start /status /admin /webhook

## If bot doesn't respond
1) Bot: /webhook should show correct URL and no last_error_message.
2) Railway logs: look for `POST /tg/webhook 200`.
3) GET /healthz must be 200.

## If deploy stuck on "Deploying"
Set Railway Healthcheck Path = /healthz

## Secrets
- BOT_TOKEN must never be committed.
- If leaked -> revoke in BotFather and update Railway vars.
""",

"docs/ARCHITECTURE.md": """# Architecture

## Components
- FastAPI + Uvicorn (bot/server.py)
  - POST /tg/webhook
  - GET /healthz /version /readyz /metrics
- python-telegram-bot Application (bot/app_factory.py)
- Infrastructure (bot/infrastructure.py)
  - Postgres / Redis checks + runtime_report
- Alembic migrations: migrations/

## Runtime flow
1) Uvicorn starts FastAPI app (Dockerfile CMD).
2) FastAPI lifespan:
   - init_infrastructure()
   - ptb_app.initialize()
   - ptb_app.start()
3) Telegram -> POST /tg/webhook -> Update.de_json -> ptb_app.process_update(update)

## Observability
- HTTP: /healthz /readyz /metrics
- Bot: /vars /webhook /diag
- Railway logs: uvicorn access logs + app logs
""",

"docs/ENDPOINTS.md": """# Endpoints & Commands

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
""",

"docs/RAILWAY.md": """# Railway

## Service
- Repo: osifeu-prog/gardient2
- Branch: main
- Domain: gardient2-production.up.railway.app
- Target port: 8080
- Recommended Healthcheck Path: /healthz

## Build/Run
- Dockerfile detected and used
- CMD should run uvicorn: bot.server:app

## Variables (names only)
- BOT_TOKEN
- ADMIN_CHAT_ID
- DATABASE_URL
- REDIS_URL
- ENV
- MODE
- WEBHOOK_URL
- LOG_LEVEL
- OPENAI_API_KEY
""",

"docs/INCIDENTS.md": """# Incidents / Notes

- Encoding/mojibake issues -> moved banner to assets/banner.txt, UI switched to English-only.
- Polling 409 conflicts -> webhook-only mode.
- FastAPI missing deps -> requirements updated.
- Prometheus duplicate timeseries -> dedicated CollectorRegistry.
- Uvicorn serving -> Dockerfile CMD uses uvicorn bot.server:app.
- Indentation/syntax regressions -> restored stable server baseline.
"""
}

for path, content in docs.items():
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.replace("\\r\\n","\\n"), encoding="utf-8")
print("OK: docs written")
