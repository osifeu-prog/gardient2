# SLH Guardian ? STATUS SNAPSHOT

## Timestamp (UTC)
2026-02-24T18:44:14.788401+00:00

## Production Base URL
https://gardient2-production.up.railway.app

## Webhook URL
https://gardient2-production.up.railway.app/tg/webhook

## /version
{"service":"gardient2","git_sha":"10637fcde0ea6a80173780543274e0215de05bf1","uptime_s":655}

## /healthz
{"ok":true,"uptime_s":655,"git_sha":"10637fcde0ea"}

## /readyz
{"ok":true,"elapsed_ms":0}

## Metrics (snippet)
# HELP http_requests_total HTTP requests total
# TYPE http_requests_total counter
# HELP http_request_latency_ms HTTP request latency ms
# TYPE http_request_latency_ms histogram
# HELP bot_commands_total Bot commands total
# TYPE bot_commands_total counter

# --- bot_commands_total ---
# TYPE http_requests_total counter
# HELP http_request_latency_ms HTTP request latency ms
# TYPE http_request_latency_ms histogram
# HELP bot_commands_total Bot commands total
# TYPE bot_commands_total counter

## Recent Git Commits
791cfe1 docs: add production status snapshot
10637fc Update app_factory.py
89914ae chore: replace ? with â€” in start title
08496c5 chore: fix title dash (?-to-emdash)
4ea639e feat(metrics): add bot_commands_total counter
d66c6e3 Update main.py
c4d5551 chore: fix title dash (replace ? with â€”)
196244e docs: regenerate complete docs set
3caace8 docs: add runbook + architecture + endpoints + railway + incidents
c95201a feat(api): readyz returns elapsed_ms

## HTTP Endpoints
- GET /healthz
- GET /version
- GET /readyz
- GET /metrics
- POST /tg/webhook

## Bot Commands
/start
/menu
/status
/whoami
/health
/admin
/vars
/webhook
/diag
/pingdb
/pingredis

---
Generated automatically.
