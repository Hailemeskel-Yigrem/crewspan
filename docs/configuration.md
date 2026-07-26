# Configuration

All settings use the `FIELDSPAN_` environment prefix.

## Required Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FIELDSPAN_DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://fieldspan:fieldspan@localhost:5432/fieldspan` |
| `FIELDSPAN_REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `FIELDSPAN_SECRET_KEY` | JWT signing key | `change-me-in-production` |

## Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FIELDSPAN_ENVIRONMENT` | `development` / `staging` / `production` | `development` |
| `FIELDSPAN_DEBUG` | Enable SQL echo | `false` |
| `FIELDSPAN_LOG_LEVEL` | Logging level | `INFO` |
| `FIELDSPAN_LOG_JSON` | JSON log format | `true` |
| `FIELDSPAN_CORS_ORIGINS` | Allowed CTA origins (JSON array) | `["http://localhost:3000"]` |
| `FIELDSPAN_ACCESS_TOKEN_EXPIRE_MINUTES` | JWT TTL | `60` |
| `FIELDSPAN_DEFAULT_PAGE_SIZE` | API pagination default | `50` |

## Worker Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `FIELDSPAN_CELERY_BROKER_URL` | Celery broker | `redis://localhost:6379/1` |
| `FIELDSPAN_CELERY_RESULT_BACKEND` | Celery results | `redis://localhost:6379/2` |
| `FIELDSPAN_WEBHOOK_TIMEOUT_SECONDS` | Webhook HTTP timeout | `30` |
