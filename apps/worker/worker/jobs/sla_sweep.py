"""Background job: sla sweep."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def run(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    logger.info("job_start", extra={"job": "sla_sweep", "keys": sorted(payload)})
    processed = int(payload.get("count", 0))
    return {"job": "sla_sweep", "status": "ok", "processed": processed}
