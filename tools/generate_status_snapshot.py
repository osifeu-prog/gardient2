from pathlib import Path
import subprocess
import datetime
import requests

BASE = "https://gardient2-production.up.railway.app"

def safe_get(url):
    try:
        r = requests.get(url, timeout=10)
        return r.text.strip()
    except Exception as e:
        return f"ERROR: {e}"

now = datetime.datetime.now(datetime.UTC).isoformat()

healthz = safe_get(f"{BASE}/healthz")
version = safe_get(f"{BASE}/version")
readyz  = safe_get(f"{BASE}/readyz")
metrics = safe_get(f"{BASE}/metrics")

metrics_lines = metrics.splitlines()
# Keep first 60 lines, but also ensure bot_commands_total block is included if present
snippet = metrics_lines[:60]
if any("bot_commands_total" in ln for ln in metrics_lines):
    # append the bot commands block lines
    for i, ln in enumerate(metrics_lines):
        if "bot_commands_total" in ln:
            snippet += ["", "# --- bot_commands_total ---"]
            snippet += metrics_lines[max(0, i-3):min(len(metrics_lines), i+15)]
            break
metrics_snippet = "\n".join(snippet)

git_log = subprocess.getoutput("git log --oneline -10")

content = f"""# SLH Guardian ? STATUS SNAPSHOT

## Timestamp (UTC)
{now}

## Production Base URL
{BASE}

## Webhook URL
{BASE}/tg/webhook

## /version
{version}

## /healthz
{healthz}

## /readyz
{readyz}

## Metrics (snippet)
{metrics_snippet}

## Recent Git Commits
{git_log}

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
Path("docs/STATUS_SNAPSHOT.md").write_text(content.replace("\\r\\n","\\n"), encoding="utf-8")
print("OK: docs/STATUS_SNAPSHOT.md refreshed")
