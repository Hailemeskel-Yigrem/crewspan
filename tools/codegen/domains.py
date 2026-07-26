"""Fieldspan domain specifications for API code generation."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FieldSpec:
    name: str
    python_type: str
    sqlalchemy_type: str
    nullable: bool = False
    indexed: bool = False
    unique: bool = False
    description: str = ""
    default: str | None = None


@dataclass(frozen=True)
class MethodSpec:
    name: str
    description: str
    params: tuple[tuple[str, str], ...] = ()
    returns: str = "None"
    http_verb: str = "POST"
    path_suffix: str = ""


@dataclass(frozen=True)
class DomainSpec:
    name: str
    title: str
    description: str
    fields: tuple[FieldSpec, ...]
    methods: tuple[MethodSpec, ...]
    table_name: str = ""
    soft_delete: bool = True
    tenant_scoped: bool = True

    @property
    def class_name(self) -> str:
        parts = self.name.split("_")
        return "".join(p.capitalize() for p in parts)

    @property
    def snake(self) -> str:
        return self.name

    @property
    def plural(self) -> str:
        if self.name.endswith("y"):
            return self.name[:-1] + "ies"
        if self.name.endswith("s"):
            return self.name + "es"
        return self.name + "s"


def _f(
    name: str,
    py_type: str,
    sa_type: str,
    *,
    nullable: bool = False,
    indexed: bool = False,
    unique: bool = False,
    description: str = "",
    default: str | None = None,
) -> FieldSpec:
    return FieldSpec(
        name=name,
        python_type=py_type,
        sqlalchemy_type=sa_type,
        nullable=nullable,
        indexed=indexed,
        unique=unique,
        description=description,
        default=default,
    )


def _m(
    name: str,
    description: str,
    *,
    params: tuple[tuple[str, str], ...] = (),
    returns: str = "None",
    http_verb: str = "POST",
    path_suffix: str = "",
) -> MethodSpec:
    return MethodSpec(
        name=name,
        description=description,
        params=params,
        returns=returns,
        http_verb=http_verb,
        path_suffix=path_suffix or f"/{name.replace('_', '-')}",
    )


DOMAINS: tuple[DomainSpec, ...] = (
    DomainSpec(
        name="tenant",
        title="Tenant",
        description="Multi-tenant organization registry with subscription tier and feature flags.",
        table_name="tenants",
        tenant_scoped=False,
        fields=(
            _f("slug", "str", "String(64)", unique=True, indexed=True, description="URL-safe tenant identifier"),
            _f("display_name", "str", "String(255)", description="Human-readable organization name"),
            _f("legal_name", "str", "String(255)", nullable=True, description="Registered legal entity name"),
            _f("subscription_tier", "str", "String(32)", default="'standard'", description="Billing tier"),
            _f("timezone", "str", "String(64)", default="'UTC'", description="Default IANA timezone"),
            _f("is_active", "bool", "Boolean", default="True", description="Whether tenant may authenticate"),
            _f("feature_flags", "dict", "JSON", nullable=True, description="Per-tenant feature toggles"),
            _f("settings", "dict", "JSON", nullable=True, description="Tenant-level configuration blob"),
        ),
        methods=(
            _m("activate", "Enable tenant access and notify administrators", http_verb="POST", path_suffix="/activate"),
            _m("deactivate", "Suspend tenant access while preserving data", http_verb="POST", path_suffix="/deactivate"),
            _m("update_settings", "Merge tenant settings with validation", params=(("settings", "dict"),), returns="dict"),
        ),
    ),
    DomainSpec(
        name="user",
        title="User",
        description="Platform user accounts scoped to tenants with authentication metadata.",
        table_name="users",
        fields=(
            _f("email", "str", "String(320)", unique=True, indexed=True, description="Login email address"),
            _f("full_name", "str", "String(255)", description="Display name"),
            _f("password_hash", "str", "String(255)", description="Bcrypt password hash"),
            _f("phone", "str", "String(32)", nullable=True, description="Contact phone number"),
            _f("role_id", "UUID", "UUID(as_uuid=True)", indexed=True, description="Assigned RBAC role"),
            _f("is_active", "bool", "Boolean", default="True", description="Account enabled flag"),
            _f("last_login_at", "datetime | None", "DateTime(timezone=True)", nullable=True),
            _f("preferences", "dict", "JSON", nullable=True, description="UI and notification preferences"),
        ),
        methods=(
            _m("change_password", "Validate and rotate user password hash", params=(("new_password", "str"),)),
            _m("record_login", "Update last login timestamp", http_verb="POST", path_suffix="/record-login"),
            _m("deactivate", "Disable user without deleting audit history", http_verb="POST", path_suffix="/deactivate"),
        ),
    ),
    DomainSpec(
        name="role",
        title="Role",
        description="Role-based access control definitions with permission sets.",
        table_name="roles",
        fields=(
            _f("name", "str", "String(128)", indexed=True, description="Role identifier within tenant"),
            _f("description", "str", "Text", nullable=True, description="Role purpose summary"),
            _f("permissions", "list", "JSON", description="Granted permission keys"),
            _f("is_system", "bool", "Boolean", default="False", description="Built-in role that cannot be deleted"),
        ),
        methods=(
            _m("grant_permission", "Add permission if not already present", params=(("permission", "str"),), returns="list"),
            _m("revoke_permission", "Remove permission from role", params=(("permission", "str"),), returns="list"),
            _m("clone", "Duplicate role under a new name", params=(("new_name", "str"),), returns="Role"),
        ),
    ),
    DomainSpec(
        name="customer",
        title="Customer",
        description="Customer master records for field service accounts and billing.",
        table_name="customers",
        fields=(
            _f("account_number", "str", "String(64)", indexed=True, description="External account reference"),
            _f("name", "str", "String(255)", indexed=True, description="Customer display name"),
            _f("customer_type", "str", "String(32)", default="'commercial'", description="residential|commercial|government"),
            _f("billing_email", "str", "String(320)", nullable=True),
            _f("billing_address", "dict", "JSON", nullable=True, description="Structured billing address"),
            _f("credit_limit", "Decimal", "Numeric(14, 2)", nullable=True),
            _f("payment_terms_days", "int", "Integer", default="30"),
            _f("notes", "str", "Text", nullable=True),
            _f("is_active", "bool", "Boolean", default="True"),
        ),
        methods=(
            _m("update_credit_limit", "Adjust credit limit with audit trail", params=(("limit", "Decimal"),)),
            _m("merge_into", "Merge duplicate customer records", params=(("target_id", "UUID"),)),
            _m("archive", "Soft-archive inactive customer", http_verb="POST", path_suffix="/archive"),
        ),
    ),
    DomainSpec(
        name="customer_site",
        title="CustomerSite",
        description="Physical service locations belonging to customers.",
        table_name="customer_sites",
        fields=(
            _f("customer_id", "UUID", "UUID(as_uuid=True)", indexed=True),
            _f("site_code", "str", "String(64)", indexed=True),
            _f("name", "str", "String(255)"),
            _f("address", "dict", "JSON", description="Structured service address"),
            _f("latitude", "Decimal | None", "Numeric(10, 7)", nullable=True),
            _f("longitude", "Decimal | None", "Numeric(10, 7)", nullable=True),
            _f("access_instructions", "str", "Text", nullable=True),
            _f("service_window", "dict", "JSON", nullable=True, description="Preferred service hours"),
            _f("is_active", "bool", "Boolean", default="True"),
        ),
        methods=(
            _m("geocode", "Resolve coordinates from address", http_verb="POST", path_suffix="/geocode"),
            _m("validate_access_window", "Check if datetime falls within service window", params=(("at", "datetime"),), returns="bool"),
        ),
    ),
    DomainSpec(
        name="contact",
        title="Contact",
        description="Customer contacts for scheduling and notification routing.",
        table_name="contacts",
        fields=(
            _f("customer_id", "UUID", "UUID(as_uuid=True)", indexed=True),
            _f("site_id", "UUID", "UUID(as_uuid=True)", nullable=True, indexed=True),
            _f("first_name", "str", "String(128)"),
            _f("last_name", "str", "String(128)"),
            _f("email", "str", "String(320)", nullable=True),
            _f("phone", "str", "String(32)", nullable=True),
            _f("role_title", "str", "String(128)", nullable=True),
            _f("is_primary", "bool", "Boolean", default="False"),
            _f("notify_on_dispatch", "bool", "Boolean", default="True"),
        ),
        methods=(
            _m("set_primary", "Mark contact as primary for customer", http_verb="POST", path_suffix="/set-primary"),
            _m("opt_out_notifications", "Disable all notification channels", http_verb="POST", path_suffix="/opt-out"),
        ),
    ),
    DomainSpec(
        name="work_order",
        title="WorkOrder",
        description="Core work order lifecycle from intake through completion.",
        table_name="work_orders",
        fields=(
            _f("order_number", "str", "String(64)", unique=True, indexed=True),
            _f("customer_id", "UUID", "UUID(as_uuid=True)", indexed=True),
            _f("site_id", "UUID", "UUID(as_uuid=True)", indexed=True),
            _f("title", "str", "String(255)"),
            _f("description", "str", "Text", nullable=True),
            _f("priority", "str", "String(16)", default="'normal'", description="low|normal|high|critical"),
            _f("status", "str", "String(32)", default="'draft'", indexed=True),
            _f("scheduled_start", "datetime | None", "DateTime(timezone=True)", nullable=True),
            _f("scheduled_end", "datetime | None", "DateTime(timezone=True)", nullable=True),
            _f("assigned_technician_id", "UUID", "UUID(as_uuid=True)", nullable=True, indexed=True),
            _f("sla_policy_id", "UUID", "UUID(as_uuid=True)", nullable=True),
            _f("estimated_duration_minutes", "int", "Integer", nullable=True),
            _f("completion_notes", "str", "Text", nullable=True),
        ),
        methods=(
            _m("submit", "Transition draft work order to submitted queue", http_verb="POST", path_suffix="/submit"),
            _m("assign_technician", "Assign technician with conflict check", params=(("technician_id", "UUID"),)),
            _m("start", "Mark work order in progress", http_verb="POST", path_suffix="/start"),
            _m("complete", "Complete work order with notes", params=(("notes", "str | None"),), http_verb="POST", path_suffix="/complete"),
            _m("cancel", "Cancel with reason", params=(("reason", "str"),), http_verb="POST", path_suffix="/cancel"),
        ),
    ),
    DomainSpec(
        name="work_order_task",
        title="WorkOrderTask",
        description="Checklist tasks attached to work orders.",
        table_name="work_order_tasks",
        fields=(
            _f("work_order_id", "UUID", "UUID(as_uuid=True)", indexed=True),
            _f("sequence", "int", "Integer", default="0"),
            _f("title", "str", "String(255)"),
            _f("instructions", "str", "Text", nullable=True),
            _f("is_required", "bool", "Boolean", default="True"),
            _f("status", "str", "String(32)", default="'pending'"),
            _f("completed_at", "datetime | None", "DateTime(timezone=True)", nullable=True),
            _f("completed_by_id", "UUID", "UUID(as_uuid=True)", nullable=True),
        ),
        methods=(
            _m("complete", "Mark task completed", http_verb="POST", path_suffix="/complete"),
            _m("reopen", "Revert completed task to pending", http_verb="POST", path_suffix="/reopen"),
            _m("reorder", "Change task sequence", params=(("sequence", "int"),), http_verb="PATCH", path_suffix="/reorder"),
        ),
    ),
    DomainSpec(
        name="technician",
        title="Technician",
        description="Field technician profiles linked to user accounts.",
        table_name="technicians",
        fields=(
            _f("user_id", "UUID", "UUID(as_uuid=True)", unique=True, indexed=True),
            _f("employee_id", "str", "String(64)", indexed=True),
            _f("home_base_latitude", "Decimal | None", "Numeric(10, 7)", nullable=True),
            _f("home_base_longitude", "Decimal | None", "Numeric(10, 7)", nullable=True),
            _f("max_daily_hours", "int", "Integer", default="8"),
            _f("status", "str", "String(32)", default="'available'", indexed=True),
            _f("certifications", "list", "JSON", nullable=True),
            _f("vehicle_info", "dict", "JSON", nullable=True),
        ),
        methods=(
            _m("set_status", "Update availability status", params=(("status", "str"),)),
            _m("update_location", "Record current GPS coordinates", params=(("lat", "Decimal"), ("lng", "Decimal"),)),
            _m("calculate_utilization", "Compute utilization for date range", params=(("start", "date"), ("end", "date"),), returns="dict"),
        ),
    ),
    DomainSpec(
        name="technician_skill",
        title="TechnicianSkill",
        description="Skill and certification assignments for technicians.",
        table_name="technician_skills",
        fields=(
            _f("technician_id", "UUID", "UUID(as_uuid=True)", indexed=True),
            _f("skill_code", "str", "String(64)", indexed=True),
            _f("skill_name", "str", "String(128)"),
            _f("proficiency_level", "int", "Integer", default="1", description="1-5 scale"),
            _f("certified_at", "date | None", "Date", nullable=True),
            _f("expires_at", "date | None", "Date", nullable=True),
        ),
        methods=(
            _m("renew_certification", "Extend certification expiry", params=(("expires_at", "date"),)),
            _m("is_valid", "Check certification not expired", returns="bool", http_verb="GET", path_suffix="/is-valid"),
        ),
    ),
    DomainSpec(
        name="schedule",
        title="Schedule",
        description="Calendar blocks for technician availability and appointments.",
        table_name="schedules",
        fields=(
            _f("technician_id", "UUID", "UUID(as_uuid=True)", indexed=True),
            _f("work_order_id", "UUID", "UUID(as_uuid=True)", nullable=True, indexed=True),
            _f("event_type", "str", "String(32)", default="'appointment'"),
            _f("starts_at", "datetime", "DateTime(timezone=True)", indexed=True),
            _f("ends_at", "datetime", "DateTime(timezone=True)"),
            _f("title", "str", "String(255)"),
            _f("notes", "str", "Text", nullable=True),
            _f("is_locked", "bool", "Boolean", default="False"),
        ),
        methods=(
            _m("lock", "Prevent schedule modifications", http_verb="POST", path_suffix="/lock"),
            _m("unlock", "Allow schedule modifications", http_verb="POST", path_suffix="/unlock"),
            _m("detect_conflicts", "Find overlapping events", params=(("starts_at", "datetime"), ("ends_at", "datetime"),), returns="list"),
        ),
    ),
    DomainSpec(
        name="dispatch",
        title="Dispatch",
        description="Dispatch board assignments linking technicians to work orders.",
        table_name="dispatches",
        fields=(
            _f("work_order_id", "UUID", "UUID(as_uuid=True)", indexed=True),
            _f("technician_id", "UUID", "UUID(as_uuid=True)", indexed=True),
            _f("dispatched_at", "datetime", "DateTime(timezone=True)"),
            _f("accepted_at", "datetime | None", "DateTime(timezone=True)", nullable=True),
            _f("status", "str", "String(32)", default="'pending'", indexed=True),
            _f("dispatch_notes", "str", "Text", nullable=True),
            _f("route_eta_minutes", "int", "Integer", nullable=True),
        ),
        methods=(
            _m("accept", "Technician accepts dispatch", http_verb="POST", path_suffix="/accept"),
            _m("decline", "Technician declines with reason", params=(("reason", "str"),), http_verb="POST", path_suffix="/decline"),
            _m("en_route", "Mark technician en route", http_verb="POST", path_suffix="/en-route"),
            _m("arrive", "Record on-site arrival", http_verb="POST", path_suffix="/arrive"),
        ),
    ),
    DomainSpec(
        name="inventory_item",
        title="InventoryItem",
        description="Catalog of parts and consumables tracked in inventory.",
        table_name="inventory_items",
        fields=(
            _f("sku", "str", "String(64)", unique=True, indexed=True),
            _f("name", "str", "String(255)", indexed=True),
            _f("description", "str", "Text", nullable=True),
            _f("unit_of_measure", "str", "String(16)", default="'each'"),
            _f("unit_cost", "Decimal", "Numeric(14, 4)", default="0"),
            _f("reorder_point", "int", "Integer", default="0"),
            _f("reorder_quantity", "int", "Integer", default="0"),
            _f("is_active", "bool", "Boolean", default="True"),
            _f("category", "str", "String(64)", nullable=True, indexed=True),
        ),
        methods=(
            _m("adjust_reorder_levels", "Update reorder point and quantity", params=(("point", "int"), ("quantity", "int"),)),
            _m("deactivate", "Mark item inactive", http_verb="POST", path_suffix="/deactivate"),
            _m("calculate_stock_value", "Sum stock on hand times unit cost", returns="Decimal", http_verb="GET", path_suffix="/stock-value"),
        ),
    ),
    DomainSpec(
        name="inventory_location",
        title="InventoryLocation",
        description="Warehouses, vans, and stock locations.",
        table_name="inventory_locations",
        fields=(
            _f("code", "str", "String(64)", indexed=True),
            _f("name", "str", "String(255)"),
            _f("location_type", "str", "String(32)", default="'warehouse'"),
            _f("technician_id", "UUID", "UUID(as_uuid=True)", nullable=True, indexed=True),
            _f("address", "dict", "JSON", nullable=True),
            _f("is_active", "bool", "Boolean", default="True"),
        ),
        methods=(
            _m("assign_to_technician", "Link location to technician van stock", params=(("technician_id", "UUID"),)),
            _m("list_low_stock", "Return items below reorder point at location", returns="list", http_verb="GET", path_suffix="/low-stock"),
        ),
    ),
    DomainSpec(
        name="stock_movement",
        title="StockMovement",
        description="Inventory transactions: receipts, issues, transfers, adjustments.",
        table_name="stock_movements",
        fields=(
            _f("item_id", "UUID", "UUID(as_uuid=True)", indexed=True),
            _f("from_location_id", "UUID", "UUID(as_uuid=True)", nullable=True, indexed=True),
            _f("to_location_id", "UUID", "UUID(as_uuid=True)", nullable=True, indexed=True),
            _f("quantity", "Decimal", "Numeric(14, 4)"),
            _f("movement_type", "str", "String(32)", indexed=True),
            _f("reference_type", "str", "String(64)", nullable=True),
            _f("reference_id", "UUID", "UUID(as_uuid=True)", nullable=True),
            _f("performed_by_id", "UUID", "UUID(as_uuid=True)", nullable=True),
            _f("notes", "str", "Text", nullable=True),
        ),
        methods=(
            _m("validate_quantity", "Ensure sufficient stock for issue/transfer", returns="bool", http_verb="POST", path_suffix="/validate"),
            _m("reverse", "Create compensating movement", params=(("reason", "str"),), http_verb="POST", path_suffix="/reverse"),
        ),
    ),
    DomainSpec(
        name="parts_request",
        title="PartsRequest",
        description="Parts requisitions linked to work orders.",
        table_name="parts_requests",
        fields=(
            _f("work_order_id", "UUID", "UUID(as_uuid=True)", indexed=True),
            _f("requested_by_id", "UUID", "UUID(as_uuid=True)", indexed=True),
            _f("status", "str", "String(32)", default="'pending'", indexed=True),
            _f("needed_by", "datetime | None", "DateTime(timezone=True)", nullable=True),
            _f("fulfillment_location_id", "UUID", "UUID(as_uuid=True)", nullable=True),
            _f("line_items", "list", "JSON", description="Requested parts with quantities"),
            _f("notes", "str", "Text", nullable=True),
        ),
        methods=(
            _m("approve", "Approve parts request", http_verb="POST", path_suffix="/approve"),
            _m("fulfill", "Issue parts and update inventory", http_verb="POST", path_suffix="/fulfill"),
            _m("reject", "Reject with reason", params=(("reason", "str"),), http_verb="POST", path_suffix="/reject"),
        ),
    ),
    DomainSpec(
        name="invoice",
        title="Invoice",
        description="Customer invoices generated from completed work.",
        table_name="invoices",
        fields=(
            _f("invoice_number", "str", "String(64)", unique=True, indexed=True),
            _f("customer_id", "UUID", "UUID(as_uuid=True)", indexed=True),
            _f("work_order_id", "UUID", "UUID(as_uuid=True)", nullable=True, indexed=True),
            _f("status", "str", "String(32)", default="'draft'", indexed=True),
            _f("issue_date", "date", "Date"),
            _f("due_date", "date", "Date"),
            _f("subtotal", "Decimal", "Numeric(14, 2)", default="0"),
            _f("tax_amount", "Decimal", "Numeric(14, 2)", default="0"),
            _f("total_amount", "Decimal", "Numeric(14, 2)", default="0"),
            _f("currency", "str", "String(3)", default="'USD'"),
            _f("notes", "str", "Text", nullable=True),
        ),
        methods=(
            _m("finalize", "Lock invoice totals and assign number", http_verb="POST", path_suffix="/finalize"),
            _m("send", "Email invoice to customer", http_verb="POST", path_suffix="/send"),
            _m("void", "Void draft or sent invoice", params=(("reason", "str"),), http_verb="POST", path_suffix="/void"),
            _m("recalculate_totals", "Recompute subtotal, tax, and total", returns="dict", http_verb="POST", path_suffix="/recalculate"),
        ),
    ),
    DomainSpec(
        name="invoice_line_item",
        title="InvoiceLineItem",
        description="Individual line items on customer invoices.",
        table_name="invoice_line_items",
        fields=(
            _f("invoice_id", "UUID", "UUID(as_uuid=True)", indexed=True),
            _f("description", "str", "String(512)"),
            _f("quantity", "Decimal", "Numeric(14, 4)", default="1"),
            _f("unit_price", "Decimal", "Numeric(14, 4)"),
            _f("tax_rate", "Decimal", "Numeric(6, 4)", default="0"),
            _f("line_total", "Decimal", "Numeric(14, 2)", default="0"),
            _f("item_type", "str", "String(32)", default="'service'"),
            _f("reference_id", "UUID", "UUID(as_uuid=True)", nullable=True),
        ),
        methods=(
            _m("recalculate", "Update line total from quantity and price", http_verb="POST", path_suffix="/recalculate"),
        ),
    ),
    DomainSpec(
        name="payment",
        title="Payment",
        description="Payment records applied to invoices.",
        table_name="payments",
        fields=(
            _f("invoice_id", "UUID", "UUID(as_uuid=True)", indexed=True),
            _f("amount", "Decimal", "Numeric(14, 2)"),
            _f("payment_method", "str", "String(32)"),
            _f("payment_date", "date", "Date"),
            _f("reference_number", "str", "String(128)", nullable=True),
            _f("status", "str", "String(32)", default="'completed'"),
            _f("processor_response", "dict", "JSON", nullable=True),
        ),
        methods=(
            _m("refund", "Issue partial or full refund", params=(("amount", "Decimal"), ("reason", "str"),)),
            _m("reconcile", "Mark payment reconciled with bank feed", http_verb="POST", path_suffix="/reconcile"),
        ),
    ),
    DomainSpec(
        name="sla_policy",
        title="SlaPolicy",
        description="Service level agreement policy definitions.",
        table_name="sla_policies",
        fields=(
            _f("name", "str", "String(128)", indexed=True),
            _f("description", "str", "Text", nullable=True),
            _f("priority", "str", "String(16)", indexed=True),
            _f("response_minutes", "int", "Integer"),
            _f("resolution_minutes", "int", "Integer"),
            _f("business_hours_only", "bool", "Boolean", default="True"),
            _f("escalation_rules", "list", "JSON", nullable=True),
            _f("is_active", "bool", "Boolean", default="True"),
        ),
        methods=(
            _m("evaluate_deadlines", "Compute response/resolution deadlines", params=(("opened_at", "datetime"),), returns="dict"),
            _m("clone", "Duplicate policy", params=(("new_name", "str"),), returns="SlaPolicy"),
        ),
    ),
    DomainSpec(
        name="sla_breach",
        title="SlaBreach",
        description="Recorded SLA violations for reporting and escalation.",
        table_name="sla_breaches",
        fields=(
            _f("work_order_id", "UUID", "UUID(as_uuid=True)", indexed=True),
            _f("sla_policy_id", "UUID", "UUID(as_uuid=True)", indexed=True),
            _f("breach_type", "str", "String(32)", indexed=True),
            _f("expected_at", "datetime", "DateTime(timezone=True)"),
            _f("detected_at", "datetime", "DateTime(timezone=True)"),
            _f("minutes_overdue", "int", "Integer"),
            _f("acknowledged", "bool", "Boolean", default="False"),
            _f("escalation_level", "int", "Integer", default="0"),
        ),
        methods=(
            _m("acknowledge", "Mark breach reviewed", http_verb="POST", path_suffix="/acknowledge"),
            _m("escalate", "Increment escalation level and notify", http_verb="POST", path_suffix="/escalate"),
        ),
    ),
    DomainSpec(
        name="service_contract",
        title="ServiceContract",
        description="Recurring service agreements with customers.",
        table_name="service_contracts",
        fields=(
            _f("customer_id", "UUID", "UUID(as_uuid=True)", indexed=True),
            _f("contract_number", "str", "String(64)", unique=True, indexed=True),
            _f("name", "str", "String(255)"),
            _f("start_date", "date", "Date"),
            _f("end_date", "date | None", "Date", nullable=True),
            _f("billing_frequency", "str", "String(32)", default="'monthly'"),
            _f("annual_value", "Decimal", "Numeric(14, 2)", nullable=True),
            _f("covered_sites", "list", "JSON", nullable=True),
            _f("terms", "dict", "JSON", nullable=True),
            _f("status", "str", "String(32)", default="'active'", indexed=True),
        ),
        methods=(
            _m("renew", "Extend contract end date", params=(("new_end_date", "date"),)),
            _m("terminate", "End contract early", params=(("reason", "str"),), http_verb="POST", path_suffix="/terminate"),
            _m("generate_work_orders", "Create preventive maintenance work orders", returns="list", http_verb="POST", path_suffix="/generate-work-orders"),
        ),
    ),
    DomainSpec(
        name="equipment",
        title="Equipment",
        description="Customer-owned equipment and assets under service.",
        table_name="equipment",
        fields=(
            _f("customer_id", "UUID", "UUID(as_uuid=True)", indexed=True),
            _f("site_id", "UUID", "UUID(as_uuid=True)", nullable=True, indexed=True),
            _f("asset_tag", "str", "String(64)", indexed=True),
            _f("name", "str", "String(255)"),
            _f("manufacturer", "str", "String(128)", nullable=True),
            _f("model_number", "str", "String(128)", nullable=True),
            _f("serial_number", "str", "String(128)", nullable=True, indexed=True),
            _f("install_date", "date | None", "Date", nullable=True),
            _f("warranty_expires", "date | None", "Date", nullable=True),
            _f("specifications", "dict", "JSON", nullable=True),
            _f("status", "str", "String(32)", default="'active'"),
        ),
        methods=(
            _m("record_service", "Log service event on equipment", params=(("work_order_id", "UUID"), ("notes", "str"),)),
            _m("retire", "Mark equipment out of service", params=(("reason", "str"),), http_verb="POST", path_suffix="/retire"),
        ),
    ),
    DomainSpec(
        name="notification",
        title="Notification",
        description="Outbound notification delivery records.",
        table_name="notifications",
        fields=(
            _f("recipient_id", "UUID", "UUID(as_uuid=True)", nullable=True, indexed=True),
            _f("recipient_email", "str", "String(320)", nullable=True),
            _f("channel", "str", "String(32)", indexed=True),
            _f("template_key", "str", "String(128)"),
            _f("subject", "str", "String(512)", nullable=True),
            _f("body", "str", "Text"),
            _f("status", "str", "String(32)", default="'pending'", indexed=True),
            _f("sent_at", "datetime | None", "DateTime(timezone=True)", nullable=True),
            _f("payload_meta", "dict", "JSON", nullable=True, description="Channel-specific payload attributes"),
        ),
        methods=(
            _m("mark_sent", "Record successful delivery", http_verb="POST", path_suffix="/mark-sent"),
            _m("mark_failed", "Record delivery failure", params=(("error", "str"),), http_verb="POST", path_suffix="/mark-failed"),
            _m("retry", "Requeue failed notification", http_verb="POST", path_suffix="/retry"),
        ),
    ),
    DomainSpec(
        name="webhook",
        title="Webhook",
        description="Tenant webhook subscriptions for outbound event delivery.",
        table_name="webhooks",
        fields=(
            _f("name", "str", "String(128)"),
            _f("url", "str", "String(2048)"),
            _f("secret", "str", "String(255)"),
            _f("event_types", "list", "JSON"),
            _f("is_active", "bool", "Boolean", default="True"),
            _f("failure_count", "int", "Integer", default="0"),
            _f("last_triggered_at", "datetime | None", "DateTime(timezone=True)", nullable=True),
        ),
        methods=(
            _m("trigger_test", "Send test payload", http_verb="POST", path_suffix="/test"),
            _m("rotate_secret", "Generate new signing secret", returns="str", http_verb="POST", path_suffix="/rotate-secret"),
            _m("disable_on_failures", "Auto-disable after threshold", params=(("threshold", "int"),), http_verb="POST", path_suffix="/disable-on-failures"),
        ),
    ),
    DomainSpec(
        name="audit_log",
        title="AuditLog",
        description="Immutable audit trail for compliance and forensics.",
        table_name="audit_logs",
        soft_delete=False,
        fields=(
            _f("actor_id", "UUID", "UUID(as_uuid=True)", nullable=True, indexed=True),
            _f("action", "str", "String(64)", indexed=True),
            _f("resource_type", "str", "String(64)", indexed=True),
            _f("resource_id", "UUID", "UUID(as_uuid=True)", nullable=True, indexed=True),
            _f("changes", "dict", "JSON", nullable=True),
            _f("ip_address", "str", "String(45)", nullable=True),
            _f("user_agent", "str", "String(512)", nullable=True),
        ),
        methods=(
            _m("search_by_resource", "Find audit entries for resource", params=(("resource_type", "str"), ("resource_id", "UUID"),), returns="list", http_verb="GET", path_suffix="/by-resource"),
        ),
    ),
)


def get_domain(name: str) -> DomainSpec:
    for domain in DOMAINS:
        if domain.name == name:
            return domain
    raise KeyError(f"Unknown domain: {name}")


def all_domains() -> tuple[DomainSpec, ...]:
    return DOMAINS
