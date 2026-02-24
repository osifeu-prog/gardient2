# Architecture

## Components
- FastAPI (bot/server.py) serves:
  - POST /tg/webhook (Telegram updates)
  - GET /healthz, /version, /readyz, /metrics
- python-telegram-bot (PTB) Application created in bot/app_factory.py
- Infrastructure checks in bot/infrastructure.py:
  - Postgres
  - Redis
- Alembic migrations under migrations/

## Runtime flow
1) Uvicorn starts FastAPI app (Dockerfile CMD).
2) FastAPI lifespan:
   - init_infrastructure()
   - ptb_app.initialize()
   - ptb_app.start()
3) Telegram sends updates -> POST /tg/webhook -> Update.de_json -> ptb_app.process_update(update)

## Observability
- /metrics: Prometheus metrics
- Railway logs: Uvicorn access logs + app logs

