# Incidents / Notes

- Encoding/mojibake issues -> moved banner to assets/banner.txt, UI switched to English-only.
- Polling 409 conflicts -> webhook-only mode.
- FastAPI missing deps -> requirements updated.
- Prometheus duplicate timeseries -> dedicated CollectorRegistry.
- Uvicorn serving -> Dockerfile CMD uses uvicorn bot.server:app.
- Indentation/syntax regressions -> restored stable server baseline.
