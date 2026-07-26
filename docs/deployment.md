# Deployment

## Docker Compose (Development)

```bash
docker compose up -d
```

Services: `api`, `web`, `worker`, `worker-beat`, `postgres`, `redis`

## Production Checklist

1. Set strong `CREWSPAN_SECRET_KEY` (32+ random bytes)
2. Configure managed PostgreSQL with SSL
3. Use Redis Cluster or ElastiCache for Celery broker
4. Enable HTTPS termination at load balancer
5. Set `CREWSPAN_CORS_ORIGINS` to production domain
6. Configure log aggregation (JSON structured logs)
7. Set up database backups and point-in-time recovery

## Kubernetes

Build images:

```bash
docker build -t crewspan-api:latest apps/api
docker build -t crewspan-web:latest apps/web
docker build -t crewspan-worker:latest apps/worker
```

Deploy with secrets mounted for database URL, Redis URL, and JWT secret.

## Health Checks

- `GET /health` — liveness (always 200 if process running)
- `GET /ready` — readiness (checks DB connectivity in production)

## Environment Matrix

| Setting | Development | Staging | Production |
|---------|-------------|---------|------------|
| `CREWSPAN_DEBUG` | true | false | false |
| `CREWSPAN_LOG_JSON` | false | true | true |
| DB | Docker postgres | Managed PG | Managed PG + SSL |
| Redis | Docker redis | ElastiCache | ElastiCache cluster |
| HTTPS | Vite proxy | TLS at LB | TLS at LB |
| Replicas | 1 | 2 | 3+ |

## Docker Compose Services

| Service | Image | Port | Notes |
|---------|-------|------|-------|
| postgres | postgres:15 | 5432 | Persistent volume |
| redis | redis:7 | 6379 | Broker + cache |
| api | crewspan-api | 8000 | Uvicorn, hot reload in dev |
| web | crewspan-web | 3000/80 | Vite dev or nginx prod |
| worker | crewspan-worker | — | Celery consumer |
| worker-beat | crewspan-worker | — | Celery beat scheduler |

## Kubernetes Manifests (Outline)

```yaml
# api-deployment.yaml (excerpt)
spec:
  replicas: 3
  template:
    spec:
      containers:
        - name: api
          image: crewspan-api:0.4.0
          envFrom:
            - secretRef:
                name: crewspan-secrets
          livenessProbe:
            httpGet: {{ path: /health, port: 8000 }}
          readinessProbe:
            httpGet: {{ path: /ready, port: 8000 }}
```

Secrets should include: `CREWSPAN_DATABASE_URL`, `CREWSPAN_REDIS_URL`, `CREWSPAN_SECRET_KEY`.

## Database Migrations in CI/CD

```bash
# Run before rolling out new API version
kubectl exec deploy/crewspan-api -- alembic upgrade head
```

Never run migrations concurrently from multiple pods — use a CI job or init container.

## Backup & Recovery

1. Enable automated daily snapshots on PostgreSQL
2. Test restore quarterly to staging
3. Redis is ephemeral (broker only) — no backup required
4. Export critical tenant data via `/api/v1/exports/*` before major migrations

## Scaling Guidelines

| Bottleneck | Symptom | Mitigation |
|------------|---------|------------|
| API CPU | High p95 latency | Horizontal pod autoscaling |
| DB connections | Pool exhaustion | PgBouncer, increase pool_size cautiously |
| Worker backlog | Queue depth growing | Add workers per queue |
| Web bundle size | Slow first load | CDN, code splitting (already via Vite) |

## Zero-Downtime Deploys

1. Build and push new images with semver tags
2. Run migrations (backward-compatible only)
3. Rolling update API/worker deployments
4. Invalidate CDN cache for web static assets
5. Monitor error rate and SLA breach metrics for 30 minutes
