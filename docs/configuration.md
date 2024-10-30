# Configuration

All settings use the `RELAYOPS_` environment prefix.

## Required Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `RELAYOPS_DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://relayops:relayops@localhost:5432/relayops` |
| `RELAYOPS_REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `RELAYOPS_SECRET_KEY` | JWT signing key | `change-me-in-production` |

## Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `RELAYOPS_ENVIRONMENT` | `development` / `staging` / `production` | `development` |
| `RELAYOPS_DEBUG` | Enable SQL echo | `false` |
| `RELAYOPS_LOG_LEVEL` | Logging level | `INFO` |
| `RELAYOPS_LOG_JSON` | JSON log format | `true` |
| `RELAYOPS_CORS_ORIGINS` | Allowed CTA origins (JSON array) | `["http://localhost:3000"]` |
| `RELAYOPS_ACCESS_TOKEN_EXPIRE_MINUTES` | JWT TTL | `60` |
| `RELAYOPS_DEFAULT_PAGE_SIZE` | API pagination default | `50` |

## Worker Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `RELAYOPS_CELERY_BROKER_URL` | Celery broker | `redis://localhost:6379/1` |
| `RELAYOPS_CELERY_RESULT_BACKEND` | Celery results | `redis://localhost:6379/2` |
| `RELAYOPS_WEBHOOK_TIMEOUT_SECONDS` | Webhook HTTP timeout | `30` |
