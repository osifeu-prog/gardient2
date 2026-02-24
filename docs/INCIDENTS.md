# Incidents / Notes

Keep short notes of notable failures and the fix:
- Encoding / mojibake in banner & Hebrew text -> moved banner to assets/banner.txt
- Webhook 409 conflicts -> switched to webhook-only
- FastAPI missing deps -> requirements.txt updated
- Prometheus duplicate timeseries -> dedicated registry (CollectorRegistry)
- Indentation/syntax regressions -> restored server baseline

