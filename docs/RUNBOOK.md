# SLH Guardian (gardient2) — RUNBOOK

## Production
- Domain: https://gardient2-production.up.railway.app
- Webhook: https://gardient2-production.up.railway.app/tg/webhook
- Mode: webhook-only

## Quick checks
- GET /healthz  -> should return ok + uptime_s + git_sha
- GET /version  -> should return service + git_sha + uptime_s
- GET /metrics  -> Prometheus metrics text
- Bot: /start, /status, /admin, /webhook

## If bot doesn't respond
1) Check webhook:
   - /webhook command in bot
   - Telegram getWebhookInfo should show url=/tg/webhook and no last_error_message
2) Check Railway Deploy Logs:
   - Uvicorn running on 0.0.0.0:8080
   - POST /tg/webhook 200
3) Check healthz:
   - GET /healthz must be 200

## If deploy stuck on "Deploying"
Set Railway Healthcheck Path = /healthz

## Rotation / secrets
- BOT_TOKEN must never be committed.
- If token leaked -> revoke and update Railway variables.

