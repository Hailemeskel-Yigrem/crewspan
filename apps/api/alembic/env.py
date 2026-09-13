"""Alembic migration environment."""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.base import Base
from app.config import settings
from app.domains.audit_log import models as audit_log_models  # noqa: F401
from app.domains.contact import models as contact_models  # noqa: F401
from app.domains.customer import models as customer_models  # noqa: F401
from app.domains.customer_site import models as customer_site_models  # noqa: F401
from app.domains.dispatch import models as dispatch_models  # noqa: F401
from app.domains.equipment import models as equipment_models  # noqa: F401
from app.domains.inventory_item import models as inventory_item_models  # noqa: F401
from app.domains.inventory_location import models as inventory_location_models  # noqa: F401
from app.domains.invoice import models as invoice_models  # noqa: F401
from app.domains.invoice_line_item import models as invoice_line_item_models  # noqa: F401
from app.domains.notification import models as notification_models  # noqa: F401
from app.domains.parts_request import models as parts_request_models  # noqa: F401
from app.domains.payment import models as payment_models  # noqa: F401
from app.domains.role import models as role_models  # noqa: F401
from app.domains.schedule import models as schedule_models  # noqa: F401
from app.domains.service_contract import models as service_contract_models  # noqa: F401
from app.domains.sla_breach import models as sla_breach_models  # noqa: F401
from app.domains.sla_policy import models as sla_policy_models  # noqa: F401
from app.domains.stock_movement import models as stock_movement_models  # noqa: F401
from app.domains.technician import models as technician_models  # noqa: F401
from app.domains.technician_skill import models as technician_skill_models  # noqa: F401
from app.domains.tenant import models as tenant_models  # noqa: F401
from app.domains.user import models as user_models  # noqa: F401
from app.domains.webhook import models as webhook_models  # noqa: F401
from app.domains.work_order import models as work_order_models  # noqa: F401
from app.domains.work_order_task import models as work_order_task_models  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
config.set_main_option("sqlalchemy.url", settings.database_url)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
