# SLH Guardian (gardient2) ? RUNBOOK

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
