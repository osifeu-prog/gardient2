# SLH Guardian  STATUS SNAPSHOT

## Timestamp (UTC)
2026-02-24T18:39:29.069643Z

## /version
{"service":"gardient2","git_sha":"10637fcde0ea6a80173780543274e0215de05bf1","uptime_s":370}

## /healthz
{"ok":true,"uptime_s":369,"git_sha":"10637fcde0ea"}

## /readyz
{"ok":true,"elapsed_ms":0}

## Metrics (first 40 lines)
# HELP http_requests_total HTTP requests total
# TYPE http_requests_total counter
http_requests_total{method="GET",path="/healthz",status="200"} 1.0
http_requests_total{method="GET",path="/version",status="200"} 1.0
http_requests_total{method="GET",path="/readyz",status="200"} 1.0
# HELP http_requests_created HTTP requests total
# TYPE http_requests_created gauge
http_requests_created{method="GET",path="/healthz",status="200"} 1.7719583699938357e+09
http_requests_created{method="GET",path="/version",status="200"} 1.7719583707904124e+09
http_requests_created{method="GET",path="/readyz",status="200"} 1.77195837149266e+09
# HELP http_request_latency_ms HTTP request latency ms
# TYPE http_request_latency_ms histogram
http_request_latency_ms_bucket{le="5.0",method="GET",path="/healthz"} 1.0
http_request_latency_ms_bucket{le="10.0",method="GET",path="/healthz"} 1.0
http_request_latency_ms_bucket{le="25.0",method="GET",path="/healthz"} 1.0
http_request_latency_ms_bucket{le="50.0",method="GET",path="/healthz"} 1.0
http_request_latency_ms_bucket{le="100.0",method="GET",path="/healthz"} 1.0
http_request_latency_ms_bucket{le="250.0",method="GET",path="/healthz"} 1.0
http_request_latency_ms_bucket{le="500.0",method="GET",path="/healthz"} 1.0
http_request_latency_ms_bucket{le="1000.0",method="GET",path="/healthz"} 1.0
http_request_latency_ms_bucket{le="2000.0",method="GET",path="/healthz"} 1.0
http_request_latency_ms_bucket{le="5000.0",method="GET",path="/healthz"} 1.0
http_request_latency_ms_bucket{le="+Inf",method="GET",path="/healthz"} 1.0
http_request_latency_ms_count{method="GET",path="/healthz"} 1.0
http_request_latency_ms_sum{method="GET",path="/healthz"} 0.0
http_request_latency_ms_bucket{le="5.0",method="GET",path="/version"} 1.0
http_request_latency_ms_bucket{le="10.0",method="GET",path="/version"} 1.0
http_request_latency_ms_bucket{le="25.0",method="GET",path="/version"} 1.0
http_request_latency_ms_bucket{le="50.0",method="GET",path="/version"} 1.0
http_request_latency_ms_bucket{le="100.0",method="GET",path="/version"} 1.0
http_request_latency_ms_bucket{le="250.0",method="GET",path="/version"} 1.0
http_request_latency_ms_bucket{le="500.0",method="GET",path="/version"} 1.0
http_request_latency_ms_bucket{le="1000.0",method="GET",path="/version"} 1.0
http_request_latency_ms_bucket{le="2000.0",method="GET",path="/version"} 1.0
http_request_latency_ms_bucket{le="5000.0",method="GET",path="/version"} 1.0
http_request_latency_ms_bucket{le="+Inf",method="GET",path="/version"} 1.0
http_request_latency_ms_count{method="GET",path="/version"} 1.0
http_request_latency_ms_sum{method="GET",path="/version"} 0.0
http_request_latency_ms_bucket{le="5.0",method="GET",path="/readyz"} 1.0
http_request_latency_ms_bucket{le="10.0",method="GET",path="/readyz"} 1.0

## Recent Git Commits
89914ae chore: replace ? with â€” in start title
08496c5 chore: fix title dash (?-to-emdash)
4ea639e feat(metrics): add bot_commands_total counter
d66c6e3 Update main.py
c4d5551 chore: fix title dash (replace ? with â€”)

## Production Base URL
https://gardient2-production.up.railway.app

## Webhook
https://gardient2-production.up.railway.app/tg/webhook

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
