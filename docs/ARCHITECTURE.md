# Architecture

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
