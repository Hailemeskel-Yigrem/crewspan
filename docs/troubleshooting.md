# Troubleshooting

## API won't start

**Symptom:** `RuntimeError: Database not initialized`

Ensure PostgreSQL is running and `CREWSPAN_DATABASE_URL` is correct:

```bash
scripts/healthcheck.sh
```

## Migration failures

**Symptom:** `alembic.util.exc.CommandError: Can't locate revision`

Reset development database:

```bash
docker compose down -v
docker compose up -d postgres
make migrate
```

## Worker tasks not processing

1. Check Redis connectivity: `redis-cli ping`
2. Verify worker is consuming correct queues:
   ```bash
   celery -A worker.celery_app:celery_app inspect active_queues
   ```
3. Check worker logs for task failures

## Frontend API errors (CORS)

Ensure `CREWSPAN_CORS_ORIGINS` includes your frontend URL. In development, Vite proxies `/api` to port 8000.

## Authentication failures

- Verify `X-Tenant-Id` header is sent with every authenticated request
- Check token expiry (`CREWSPAN_ACCESS_TOKEN_EXPIRE_MINUTES`)
- Confirm `CREWSPAN_SECRET_KEY` matches between token creation and validation

## High database connection count

Adjust pool settings in `app/db.py`: `pool_size=10`, `max_overflow=20`. Use PgBouncer in production.
