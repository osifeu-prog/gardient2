# Railway

## Service
- Repo: osifeu-prog/gardient2
- Branch: main
- Domain: gardient2-production.up.railway.app
- Port: 8080
- Recommended Healthcheck Path: /healthz

## Key Variables (names only)
- BOT_TOKEN
- ADMIN_CHAT_ID
- DATABASE_URL
- REDIS_URL
- ENV
- MODE
- WEBHOOK_URL
- LOG_LEVEL
- OPENAI_API_KEY

## Build/Run
- Dockerfile is detected and used.
- CMD should run uvicorn: bot.server:app

