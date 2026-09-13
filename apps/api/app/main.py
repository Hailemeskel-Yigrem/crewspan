"""Crewspan API application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.errors import register_exception_handlers
from app.db import close_db, init_db
from app.domains.audit_log.router import router as audit_log_router
from app.domains.contact.router import router as contact_router
from app.domains.customer.router import router as customer_router
from app.domains.customer_site.router import router as customer_site_router
from app.domains.dispatch.router import router as dispatch_router
from app.domains.equipment.router import router as equipment_router
from app.domains.inventory_item.router import router as inventory_item_router
from app.domains.inventory_location.router import router as inventory_location_router
from app.domains.invoice.router import router as invoice_router
from app.domains.invoice_line_item.router import router as invoice_line_item_router
from app.domains.notification.router import router as notification_router
from app.domains.parts_request.router import router as parts_request_router
from app.domains.payment.router import router as payment_router
from app.domains.role.router import router as role_router
from app.domains.schedule.router import router as schedule_router
from app.domains.service_contract.router import router as service_contract_router
from app.domains.sla_breach.router import router as sla_breach_router
from app.domains.sla_policy.router import router as sla_policy_router
from app.domains.stock_movement.router import router as stock_movement_router
from app.domains.technician.router import router as technician_router
from app.domains.technician_skill.router import router as technician_skill_router
from app.domains.tenant.router import router as tenant_router
from app.domains.user.router import router as user_router
from app.domains.webhook.router import router as webhook_router
from app.domains.work_order.router import router as work_order_router
from app.domains.work_order_task.router import router as work_order_task_router
from app.logging_config import configure_logging
from app.middleware import RequestContextMiddleware, TenantContextMiddleware

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    await init_db()
    logger.info("crewspan.startup", environment=settings.environment)
    yield
    await close_db()
    logger.info("crewspan.shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Crewspan API",
        description="Multi-tenant field service operations platform",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(TenantContextMiddleware)
    app.add_middleware(RequestContextMiddleware)
    register_exception_handlers(app)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "crewspan-api"}

    @app.get("/ready")
    async def ready() -> dict[str, str]:
        return {"status": "ready"}

    app.include_router(tenant_router, prefix="/api/v1")
    app.include_router(user_router, prefix="/api/v1")
    app.include_router(role_router, prefix="/api/v1")
    app.include_router(customer_router, prefix="/api/v1")
    app.include_router(customer_site_router, prefix="/api/v1")
    app.include_router(contact_router, prefix="/api/v1")
    app.include_router(work_order_router, prefix="/api/v1")
    app.include_router(work_order_task_router, prefix="/api/v1")
    app.include_router(technician_router, prefix="/api/v1")
    app.include_router(technician_skill_router, prefix="/api/v1")
    app.include_router(schedule_router, prefix="/api/v1")
    app.include_router(dispatch_router, prefix="/api/v1")
    app.include_router(inventory_item_router, prefix="/api/v1")
    app.include_router(inventory_location_router, prefix="/api/v1")
    app.include_router(stock_movement_router, prefix="/api/v1")
    app.include_router(parts_request_router, prefix="/api/v1")
    app.include_router(invoice_router, prefix="/api/v1")
    app.include_router(invoice_line_item_router, prefix="/api/v1")
    app.include_router(payment_router, prefix="/api/v1")
    app.include_router(sla_policy_router, prefix="/api/v1")
    app.include_router(sla_breach_router, prefix="/api/v1")
    app.include_router(service_contract_router, prefix="/api/v1")
    app.include_router(equipment_router, prefix="/api/v1")
    app.include_router(notification_router, prefix="/api/v1")
    app.include_router(webhook_router, prefix="/api/v1")
    app.include_router(audit_log_router, prefix="/api/v1")
    return app


app = create_app()
