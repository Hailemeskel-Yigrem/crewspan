# Configuration

All settings use the `CREWSPAN_` environment prefix.

## Required Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CREWSPAN_DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://crewspan:crewspan@localhost:5432/crewspan` |
| `CREWSPAN_REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `CREWSPAN_SECRET_KEY` | JWT signing key | `change-me-in-production` |

## Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CREWSPAN_ENVIRONMENT` | `development` / `staging` / `production` | `development` |
| `CREWSPAN_DEBUG` | Enable SQL echo | `false` |
| `CREWSPAN_LOG_LEVEL` | Logging level | `INFO` |
| `CREWSPAN_LOG_JSON` | JSON log format | `true` |
| `CREWSPAN_CORS_ORIGINS` | Allowed CTA origins (JSON array) | `["http://localhost:3000"]` |
| `CREWSPAN_ACCESS_TOKEN_EXPIRE_MINUTES` | JWT TTL | `60` |
| `CREWSPAN_DEFAULT_PAGE_SIZE` | API pagination default | `50` |

## Worker Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `CREWSPAN_CELERY_BROKER_URL` | Celery broker | `redis://localhost:6379/1` |
| `CREWSPAN_CELERY_RESULT_BACKEND` | Celery results | `redis://localhost:6379/2` |
| `CREWSPAN_WEBHOOK_TIMEOUT_SECONDS` | Webhook HTTP timeout | `30` |
