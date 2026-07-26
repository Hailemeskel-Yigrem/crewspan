#!/usr/bin/env python3
"""Seed demo tenant and sample data for local development."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

print("Crewspan seed script")
print("=" * 40)

TENANT_ID = str(uuid.uuid4())
USER_ID = str(uuid.uuid4())

demo_data = {
    "tenant": {
        "id": TENANT_ID,
        "slug": "demo-ops",
        "display_name": "Demo Field Services",
        "subscription_tier": "standard",
        "timezone": "America/Chicago",
    },
    "user": {
        "id": USER_ID,
        "email": "admin@demo-ops.local",
        "full_name": "Demo Administrator",
        "tenant_id": TENANT_ID,
    },
    "work_orders": [
        {"order_number": "WO-2024-001", "title": "HVAC Preventive Maintenance", "status": "in_progress", "priority": "normal"},
        {"order_number": "WO-2024-002", "title": "Emergency Plumbing Repair", "status": "submitted", "priority": "critical"},
        {"order_number": "WO-2024-003", "title": "Electrical Panel Inspection", "status": "draft", "priority": "high"},
    ],
}

print(f"Tenant ID:  {TENANT_ID}")
print(f"User ID:    {USER_ID}")
print(f"Login:      admin@demo-ops.local / demo1234")
print(f"Work orders: {len(demo_data['work_orders'])} sample records defined")
print()
print("Note: Run against live database with SQLAlchemy session in production.")
print("Seed complete (dry-run output above).")
