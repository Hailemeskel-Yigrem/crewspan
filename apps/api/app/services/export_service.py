"""CSV/JSON export helpers for operational data extracts."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Sequence
from uuid import UUID, uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.errors import ValidationAppError
from app.domains.work_order.models import WorkOrder
from app.domains.work_order.repository import WorkOrderRepository

logger = structlog.get_logger(__name__)


class ExportFormat(str, Enum):
    CSV = "csv"
    JSON = "json"


@dataclass(frozen=True, slots=True)
class ExportResult:
    export_id: UUID
    format: ExportFormat
    row_count: int
    content: str
    filename: str
    generated_at: datetime


class ExportService:
    """Builds bounded exports for work orders and related entities."""

    WORK_ORDER_COLUMNS = (
        "id",
        "order_number",
        "title",
        "status",
        "priority",
        "customer_id",
        "scheduled_start",
        "created_at",
    )

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._work_orders = WorkOrderRepository(session)

    async def export_work_orders(
        self,
        tenant_id: UUID,
        *,
        fmt: ExportFormat = ExportFormat.CSV,
        status: str | None = None,
        max_rows: int | None = None,
    ) -> ExportResult:
        max_rows = min(max_rows or settings.export_max_rows, settings.export_max_rows)
        filters: dict[str, Any] = {}
        if status:
            filters["status"] = status
        rows, total = await self._work_orders.list(
            tenant_id=tenant_id,
            page=1,
            page_size=max_rows,
            **filters,
        )
        if total > max_rows:
            logger.warning(
                "export.truncated",
                tenant_id=str(tenant_id),
                total=total,
                exported=len(rows),
            )
        content = self._serialize(rows, fmt)
        export_id = uuid4()
        filename = f"work_orders_{export_id.hex[:8]}.{fmt.value}"
        result = ExportResult(
            export_id=export_id,
            format=fmt,
            row_count=len(rows),
            content=content,
            filename=filename,
            generated_at=datetime.utcnow(),
        )
        logger.info("export.work_orders", export_id=str(export_id), rows=len(rows), format=fmt.value)
        return result

    def _serialize(self, rows: Sequence[WorkOrder], fmt: ExportFormat) -> str:
        dict_rows = [
            {col: getattr(row, col, None) for col in self.WORK_ORDER_COLUMNS}
            for row in rows
        ]
        if fmt == ExportFormat.JSON:
            return json.dumps(dict_rows, default=str, indent=2)
        if fmt == ExportFormat.CSV:
            buffer = io.StringIO()
            writer = csv.DictWriter(buffer, fieldnames=list(self.WORK_ORDER_COLUMNS))
            writer.writeheader()
            for row in dict_rows:
                writer.writerow({k: row[k] for k in self.WORK_ORDER_COLUMNS})
            return buffer.getvalue()
        raise ValidationAppError(f"Unsupported export format: {fmt}")
# history-note: evolutionary edit 29
