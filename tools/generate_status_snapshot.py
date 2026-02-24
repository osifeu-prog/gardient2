from pathlib import Path
import subprocess
import datetime
import requests
import os

BASE = "https://gardient2-production.up.railway.app"

def safe_get(url):
    try:
        r = requests.get(url, timeout=10)
        return r.text.strip()
    except Exception as e:
        return f"ERROR: {e}"

now = datetime.datetime.utcnow().isoformat() + "Z"

healthz = safe_get(f"{BASE}/healthz")
version = safe_get(f"{BASE}/version")
readyz  = safe_get(f"{BASE}/readyz")
metrics = safe_get(f"{BASE}/metrics")

# Only keep first 40 lines of metrics
metrics_snippet = "\n".join(metrics.splitlines()[:40])

git_log = subprocess.getoutput("git log --oneline -5")

content = f"""# SLH Guardian  STATUS SNAPSHOT

## Timestamp (UTC)
{now}

## /version
{version}

## /healthz
{healthz}

## /readyz
{readyz}

## Metrics (first 40 lines)
{metrics_snippet}

## Recent Git Commits
{git_log}

## Production Base URL
{BASE}

## Webhook
{BASE}/tg/webhook

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
"""

Path("docs").mkdir(exist_ok=True)
Path("docs/STATUS_SNAPSHOT.md").write_text(content, encoding="utf-8")
print("OK: docs/STATUS_SNAPSHOT.md generated")
