# Security

## Authentication

- Passwords hashed with bcrypt (passlib)
- JWT access tokens (HS256) with configurable expiry
- Bearer token required for all `/api/v1/*` routes (except health)

## Authorization

- Role-based access control (RBAC) via permission keys on roles
- Tenant isolation enforced at repository layer
- System roles cannot be deleted

## Data Protection

- All database connections use TLS in production
- Soft deletes preserve audit history
- Immutable audit log (no update/delete operations)
- Webhook payloads signed with HMAC-SHA256

## Headers

| Header | Purpose |
|--------|---------|
| `Authorization` | Bearer JWT token |
| `X-Tenant-Id` | Tenant context for multi-tenancy |
| `X-Request-Id` | Request tracing (auto-generated if absent) |

## Recommendations

1. Rotate `RELAYOPS_SECRET_KEY` periodically
2. Use short JWT expiry (≤ 60 minutes) with refresh token flow (planned)
3. Enable rate limiting at API gateway
4. Audit webhook secret rotation via `rotate_secret` endpoint
5. Never commit `.env` files or credentials
