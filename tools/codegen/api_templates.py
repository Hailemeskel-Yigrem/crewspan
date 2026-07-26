"""Template functions that emit production-quality FastAPI domain source files."""

from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tools.codegen.domains import DomainSpec, FieldSpec, MethodSpec


def finalize_source(text: str) -> str:
    """Strip template indentation so generated modules are valid Python."""
    return textwrap.dedent(text).strip() + "\n"


# Template indentation levels (outer templates use 8-space base; dedent -> column 0).
_T_BASE = 8
_T_CLASS = 12
_T_METHOD = 16
_T_BLOCK = 20


def _indent(text: str, spaces: int = 4) -> str:
    pad = " " * spaces
    return "\n".join(pad + line if line else line for line in text.splitlines())


def _snippet(text: str, *, level: int = _T_METHOD) -> str:
    """Indent a dedented code fragment for insertion into a generator template."""
    return _indent(textwrap.dedent(text).strip("\n"), level)


def _block(text: str) -> str:
    """Return a dedented fragment; the template insertion point supplies base indent."""
    return textwrap.dedent(text).strip("\n")


def _pydantic_type(field: FieldSpec) -> str:
    mapping = {
        "str": "str",
        "int": "int",
        "bool": "bool",
        "UUID": "UUID",
        "Decimal": "Decimal",
        "datetime": "datetime",
        "datetime | None": "datetime | None",
        "date": "date",
        "date | None": "date | None",
        "dict": "dict[str, object]",
        "list": "list[object]",
        "Decimal | None": "Decimal | None",
    }
    base = mapping.get(field.python_type, "object")
    if field.nullable and "| None" not in base:
        return f"{base} | None"
    return base


def _sa_type(field: FieldSpec) -> str:
    """Map domain SA type strings onto importable SQLAlchemy symbols."""
    sa_type = field.sqlalchemy_type
    # Domain specs use UUID(...); models import postgresql.UUID as PGUUID.
    if sa_type.startswith("UUID("):
        return "PG" + sa_type
    return sa_type


def _sa_column(field: FieldSpec) -> str:
    py_type = field.python_type
    if field.nullable and "| None" not in py_type:
        py_type = f"{py_type} | None"
    parts = [f"mapped_column({_sa_type(field)}"]
    if field.nullable:
        parts.append("nullable=True")
    if field.indexed:
        parts.append("index=True")
    if field.unique:
        parts.append("unique=True")
    if field.default is not None:
        parts.append(f"default={field.default}")
    parts.append(")")
    return f"{field.name}: Mapped[{py_type}] = " + ", ".join(parts)


def generate_exceptions(domain: DomainSpec) -> str:
    cn = domain.class_name
    return f'''\
        """Domain-specific exceptions for {domain.title}."""

        from __future__ import annotations

        from uuid import UUID

        from app.core.errors import DomainError, NotFoundError


        class {cn}Error(DomainError):
            """Base exception for {domain.snake} operations."""

            domain = "{domain.snake}"


        class {cn}NotFoundError(NotFoundError, {cn}Error):
            """Raised when a {domain.snake} record cannot be located."""

            def __init__(self, entity_id: UUID) -> None:
                super().__init__(
                    resource="{domain.snake}",
                    identifier=str(entity_id),
                    message=f"{domain.title} {{entity_id}} was not found",
                )


        class {cn}ValidationError({cn}Error):
            """Raised when {domain.snake} business rules are violated."""

            def __init__(self, message: str, *, code: str = "validation_error") -> None:
                super().__init__(message=message, code=code)


        class {cn}ConflictError({cn}Error):
            """Raised when an operation conflicts with current {domain.snake} state."""

            def __init__(self, message: str, *, code: str = "conflict") -> None:
                super().__init__(message=message, code=code)


        class {cn}PermissionError({cn}Error):
            """Raised when caller lacks permission for {domain.snake} action."""

            def __init__(self, action: str) -> None:
                super().__init__(
                    message=f"Permission denied for {{action}} on {domain.snake}",
                    code="permission_denied",
                )


        class {cn}StateError({cn}Error):
            """Raised when an operation is invalid for the current {domain.snake} state."""

            def __init__(self, current: str, action: str) -> None:
                super().__init__(
                    message=f"Cannot {{action}} while {domain.snake} is in status '{{current}}'",
                    code="invalid_state",
                )
                self.current = current
                self.action = action


        class {cn}TenantScopeError({cn}Error):
            """Raised when tenant context is missing or mismatched."""

            def __init__(self, message: str = "Tenant scope violation") -> None:
                super().__init__(message=message, code="tenant_scope_error")


        def not_found(entity_id: UUID) -> {cn}NotFoundError:
            """Factory for consistent not-found exceptions."""
            return {cn}NotFoundError(entity_id)


        def validation(message: str, *, code: str = "validation_error") -> {cn}ValidationError:
            """Factory for validation failures."""
            return {cn}ValidationError(message, code=code)
        '''


def generate_models(domain: DomainSpec) -> str:
    cn = domain.class_name
    table = domain.table_name or f"{domain.plural}"
    needs_date = any(
        f.sqlalchemy_type == "Date" or f.python_type.startswith("date") for f in domain.fields
    )
    datetime_import = (
        "from datetime import date, datetime" if needs_date else "from datetime import datetime"
    )
    lines: list[str] = [
        f'"""SQLAlchemy models for {domain.title}."""',
        "",
        "from __future__ import annotations",
        "",
        datetime_import,
        "from decimal import Decimal",
        "from uuid import UUID, uuid4",
        "",
        "from sqlalchemy import Boolean, Date, DateTime, Integer, JSON, Numeric, String, Text, func",
        "from sqlalchemy.dialects.postgresql import UUID as PGUUID",
        "from sqlalchemy.orm import Mapped, mapped_column",
        "",
        "from app.db import Base",
        "",
        "",
        f"class {cn}(Base):",
        f'    """{domain.description}"""',
        "",
        f'    __tablename__ = "{table}"',
        "",
        "    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)",
    ]
    if domain.tenant_scoped:
        lines.append(
            "    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True, nullable=False)"
        )
    for field in domain.fields:
        lines.append(f"    {_sa_column(field)}")
    lines.extend(
        [
            "    created_at: Mapped[datetime] = mapped_column(",
            "        DateTime(timezone=True), server_default=func.now(), nullable=False",
            "    )",
            "    updated_at: Mapped[datetime] = mapped_column(",
            "        DateTime(timezone=True),",
            "        server_default=func.now(),",
            "        onupdate=func.now(),",
            "        nullable=False,",
            "    )",
        ]
    )
    if domain.soft_delete:
        lines.extend(
            [
                "    deleted_at: Mapped[datetime | None] = mapped_column(",
                "        DateTime(timezone=True), nullable=True, index=True",
                "    )",
            ]
        )
    deleted_expr = "return self.deleted_at is not None" if domain.soft_delete else "return False"
    lines.extend(
        [
            "",
            "    def __repr__(self) -> str:",
            f'        return f"<{cn} id={{self.id}}>"',
            "",
            "    @property",
            "    def is_deleted(self) -> bool:",
            f"        {deleted_expr}",
            "",
            "    def touch_updated(self) -> None:",
            '        """Mark instance as updated (ORM onupdate also applies at flush)."""',
            "        from datetime import datetime, timezone",
            "",
            "        self.updated_at = datetime.now(timezone.utc)",
            "",
        ]
    )
    return "\n".join(lines)


def _method_request_schema(domain: DomainSpec, m: MethodSpec) -> str:
    cn = domain.class_name
    param_lines = "\n        ".join(
        f"{n}: {_map_param_type(t)}" for n, t in m.params
    )
    return _snippet(
        f"""
        class {cn}{_method_class_suffix(m.name)}Request(BaseModel):
            \"\"\"Payload for {m.name}.\"\"\"
            {param_lines}
        """,
        level=_T_BASE,
    )


def generate_schemas(domain: DomainSpec) -> str:
    cn = domain.class_name
    base_fields = []
    create_fields = []
    update_fields = []

    for f in domain.fields:
        pt = _pydantic_type(f)
        desc = f', description="{f.description}"' if f.description else ""
        req = "..." if not f.nullable and f.default is None else "None" if f.nullable else f.default or "..."
        if f.nullable or f.default is not None:
            update_fields.append(f"{f.name}: {pt} | None = None")
        base_fields.append(f"{f.name}: {pt}")
        if not f.name.endswith("_hash"):
            # Pydantic v2 requires Field(...) when metadata/defaults are attached.
            if desc or req != "...":
                create_fields.append(f"{f.name}: {pt} = Field({req}{desc})")
            else:
                create_fields.append(f"{f.name}: {pt}")

    base_block = _snippet("\n".join(base_fields), level=_T_CLASS)
    create_block = _snippet("\n".join(create_fields), level=_T_CLASS)
    update_block = (
        _snippet("\n".join(update_fields), level=_T_CLASS)
        if update_fields
        else _snippet("pass", level=_T_CLASS)
    )
    filter_fields = _snippet(
        "\n".join(
            f"{f.name}: {_pydantic_type(f)} | None = None"
            for f in domain.fields
            if f.indexed
        ),
        level=_T_CLASS,
    )

    method_schemas = [_method_request_schema(domain, m) for m in domain.methods if m.params]
    method_schemas_block = "\n\n".join(method_schemas)
    validator_imports = _snippet(_schema_validator_imports(domain), level=_T_BASE)
    field_validators = _schema_field_validators(domain)
    field_validators_block = _snippet(field_validators, level=_T_CLASS) if field_validators else ""

    return f'''\
        """Pydantic schemas for {domain.title}."""

        from __future__ import annotations

        from datetime import date, datetime
        from decimal import Decimal
        from uuid import UUID

{validator_imports}


        class {cn}Base(BaseModel):
            model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)
{base_block}


        class {cn}Create(BaseModel):
            model_config = ConfigDict(str_strip_whitespace=True)
{create_block}
{field_validators_block}


        class {cn}Update(BaseModel):
            model_config = ConfigDict(str_strip_whitespace=True)
{update_block}


        class {cn}Read({cn}Base):
            id: UUID
            {"tenant_id: UUID" if domain.tenant_scoped else ""}
            created_at: datetime
            updated_at: datetime
            {"deleted_at: datetime | None = None" if domain.soft_delete else ""}


        class {cn}ListResponse(BaseModel):
            items: list[{cn}Read]
            total: int
            page: int
            page_size: int
            pages: int = Field(default=1, ge=1)

            @classmethod
            def from_page(cls, items: list[{cn}Read], total: int, page: int, page_size: int) -> "{cn}ListResponse":
                pages = max(1, (total + page_size - 1) // page_size)
                return cls(items=items, total=total, page=page, page_size=page_size, pages=pages)


        class {cn}FilterParams(BaseModel):
            page: int = Field(default=1, ge=1)
            page_size: int = Field(default=50, ge=1, le=200)
            search: str | None = None
            order_by: str = Field(default="created_at")
            order_dir: str = Field(default="desc", pattern="^(asc|desc)$")
{filter_fields}


{method_schemas_block}
        '''


def _map_param_type(t: str) -> str:
    mapping = {
        "str": "str",
        "int": "int",
        "bool": "bool",
        "UUID": "UUID",
        "Decimal": "Decimal",
        "datetime": "datetime",
        "date": "date",
        "dict": "dict[str, object]",
        "list": "list[object]",
        "str | None": "str | None",
    }
    return mapping.get(t, t)


def _method_class_suffix(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_"))


def _enum_values(field: FieldSpec) -> list[str]:
    """Extract allowed enum-like values from field description or name heuristics."""
    if "|" in field.description:
        return [part.strip().strip("'\"") for part in field.description.split("|") if part.strip()]
    if field.name == "priority":
        return ["low", "normal", "high", "critical"]
    if field.name == "status":
        return ["draft", "pending", "active", "in_progress", "completed", "cancelled"]
    if field.name == "customer_type":
        return ["residential", "commercial", "government"]
    return []


def _schema_validator_imports(domain: DomainSpec) -> str:
    needs_re = any(
        f.name.endswith("email") or f.name == "email" or _enum_values(f)
        for f in domain.fields
    )
    needs_dates = any("date" in f.name for f in domain.fields)
    parts = ["from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator"]
    if needs_re:
        parts.append("import re")
    if needs_dates:
        parts.append("from datetime import date, datetime")
    return "\n".join(parts)


def _schema_field_validators(domain: DomainSpec) -> str:
    blocks: list[str] = []
    date_pairs = [
        ("scheduled_start", "scheduled_end"),
        ("starts_at", "ends_at"),
        ("valid_from", "valid_until"),
        ("period_start", "period_end"),
    ]
    for f in domain.fields:
        enums = _enum_values(f)
        if enums and f.python_type == "str":
            allowed = ", ".join(repr(v) for v in enums)
            blocks.append(
                f"""
        @field_validator("{f.name}")
        @classmethod
        def validate_{f.name}(cls, value: str | None) -> str | None:
            if value is None:
                return value
            allowed = {{{allowed}}}
            if value not in allowed:
                raise ValueError("{f.name} must be one of: " + ", ".join(sorted(allowed)))
            return value"""
            )
        if f.name.endswith("email") or f.name == "email":
            blocks.append(
                f"""
        @field_validator("{f.name}")
        @classmethod
        def validate_{f.name}(cls, value: str | None) -> str | None:
            if value is None:
                return value
            if "@" not in value or len(value) < 5:
                raise ValueError("Valid email address required for {f.name}")
            return value.strip().lower()"""
            )
        if f.python_type == "str" and not f.nullable and f.name not in ("password_hash",):
            blocks.append(
                f"""
        @field_validator("{f.name}")
        @classmethod
        def validate_{f.name}_not_blank(cls, value: str | None) -> str | None:
            if value is None:
                return value
            stripped = value.strip()
            if not stripped:
                raise ValueError("{f.name} cannot be blank")
            return stripped"""
            )
        if f.python_type == "Decimal" and "limit" in f.name or f.name in ("credit_limit", "amount", "unit_price"):
            blocks.append(
                f"""
        @field_validator("{f.name}")
        @classmethod
        def validate_{f.name}_positive(cls, value: Decimal | None) -> Decimal | None:
            if value is not None and value < 0:
                raise ValueError("{f.name} cannot be negative")
            return value"""
            )
    for start, end in date_pairs:
        if any(x.name == start for x in domain.fields) and any(x.name == end for x in domain.fields):
            blocks.append(
                f"""
        @model_validator(mode="after")
        def validate_{start}_{end}_ordering(self) -> "{domain.class_name}Create":
            start = getattr(self, "{start}", None)
            end = getattr(self, "{end}", None)
            if start is not None and end is not None and end < start:
                raise ValueError("{end} must be on or after {start}")
            return self"""
            )
            break
    return "\n".join(blocks)


def _service_create_validation(domain: DomainSpec) -> str:
    cn = domain.class_name
    lines: list[str] = []
    for f in domain.fields:
        if f.name.endswith("_hash"):
            continue
        enums = _enum_values(f)
        if enums and f.python_type == "str":
            allowed = ", ".join(repr(v) for v in enums)
            lines.append(
                f'if hasattr(data, "{f.name}") and getattr(data, "{f.name}") is not None:\n'
                f'    if getattr(data, "{f.name}") not in {{{allowed}}}:\n'
                f'        raise {cn}ValidationError("Invalid {f.name}: {{getattr(data, \'{f.name}\')}}")'
            )
        if f.name.endswith("email") or f.name == "email":
            lines.append(
                f'email_val = getattr(data, "{f.name}", None)\n'
                f'if email_val is not None and "@" not in email_val:\n'
                f'    raise {cn}ValidationError("Valid email required for {f.name}")'
            )
        if f.python_type == "str" and not f.nullable:
            lines.append(
                f'raw = getattr(data, "{f.name}", None)\n'
                f'if raw is not None and not str(raw).strip():\n'
                f'    raise {cn}ValidationError("{f.name} is required and cannot be blank")'
            )
    if not lines:
        return _snippet(f'logger.debug("{domain.snake}.validate_create", ok=True)', level=_T_METHOD)
    return _snippet("\n\n".join(lines), level=_T_METHOD)


def _service_update_validation(domain: DomainSpec) -> str:
    cn = domain.class_name
    lines: list[str] = []
    if any(f.name == "status" for f in domain.fields):
        lines.append(
            f"if data.status is not None and data.status == entity.status:\n"
            f'    raise {cn}ConflictError("Status is already {{entity.status}}")'
        )
    for f in domain.fields:
        enums = _enum_values(f)
        if enums:
            allowed = ", ".join(repr(v) for v in enums)
            lines.append(
                f'new_{f.name} = getattr(data, "{f.name}", None)\n'
                f"if new_{f.name} is not None and new_{f.name} not in {{{allowed}}}:\n"
                f'    raise {cn}ValidationError("Invalid {f.name}: {{new_{f.name}}}")'
            )
    if any(f.name == "scheduled_start" for f in domain.fields) and any(
        f.name == "scheduled_end" for f in domain.fields
    ):
        lines.append(
            "start = data.scheduled_start if data.scheduled_start is not None else entity.scheduled_start\n"
            "end = data.scheduled_end if data.scheduled_end is not None else entity.scheduled_end\n"
            "if start is not None and end is not None and end < start:\n"
            f'    raise {cn}ValidationError("scheduled_end must be on or after scheduled_start")'
        )
    if not lines:
        return _snippet(
            f'logger.debug("{domain.snake}.validate_update", entity_id=str(entity.id))',
            level=_T_METHOD,
        )
    return _snippet("\n\n".join(lines), level=_T_METHOD)


def _status_transition_block(domain: DomainSpec) -> str:
    cn = domain.class_name
    if not any(f.name == "status" for f in domain.fields):
        return _snippet(
            f"""
            def _set_status(self, entity: {cn}, target: str, *, action: str) -> None:
                if hasattr(entity, "status"):
                    entity.status = target
                    logger.info("{domain.snake}.status_set", entity_id=str(entity.id), status=target, action=action)
            """,
            level=_T_CLASS,
        )
    return _snippet(
        f"""
        _STATUS_TRANSITIONS: dict[str, set[str]] = {{
            "draft": {{"submitted", "cancelled", "active", "pending"}},
            "pending": {{"approved", "rejected", "cancelled", "active"}},
            "submitted": {{"in_progress", "assigned", "cancelled"}},
            "assigned": {{"in_progress", "cancelled"}},
            "in_progress": {{"completed", "cancelled", "blocked"}},
            "blocked": {{"in_progress", "cancelled"}},
            "approved": {{"fulfilled", "rejected", "cancelled"}},
            "active": {{"inactive", "completed", "cancelled", "blocked"}},
            "completed": set(),
            "cancelled": set(),
            "rejected": set(),
        }}

        def _assert_status_transition(self, entity: {cn}, target: str, *, action: str) -> None:
            current = str(getattr(entity, "status", "draft"))
            allowed = self._STATUS_TRANSITIONS.get(current, set())
            if target not in allowed and current != target:
                raise {cn}ValidationError(
                    f"Cannot {{action}} {domain.snake} from status '{{current}}' to '{{target}}'"
                )
            logger.info(
                "{domain.snake}.status_transition",
                entity_id=str(entity.id),
                from_status=current,
                to_status=target,
                action=action,
            )

        def _set_status(self, entity: {cn}, target: str, *, action: str) -> None:
            self._assert_status_transition(entity, target, action=action)
            entity.status = target
        """,
        level=_T_CLASS,
    )


def _service_validate_tenant_body(domain: DomainSpec, cn: str) -> str:
    if domain.tenant_scoped:
        return _snippet(
            f"""
            if tenant_id is None:
                raise {cn}ValidationError('X-Tenant-Id is required')
            return tenant_id
            """,
            level=_T_METHOD,
        )
    return _snippet("return tenant_id  # type: ignore[return-value]", level=_T_METHOD)


def _repo_base_select_body(domain: DomainSpec, cn: str) -> str:
    if domain.soft_delete:
        return _snippet(
            f"""
            if not include_deleted:
                stmt = stmt.where({cn}.deleted_at.is_(None))
            """,
            level=_T_METHOD,
        )
    return _snippet("pass  # hard delete domain", level=_T_METHOD)


def _repo_apply_tenant_body(domain: DomainSpec, cn: str) -> str:
    if domain.tenant_scoped:
        return _snippet(
            f"""
            if tenant_id is not None:
                stmt = stmt.where({cn}.tenant_id == tenant_id)
            """,
            level=_T_METHOD,
        )
    return _snippet("pass  # global domain", level=_T_METHOD)


def _repo_deleted_filter(domain: DomainSpec, cn: str, var: str = "stmt") -> str:
    if not domain.soft_delete:
        return ""
    return _snippet(
        f"""
        if not include_deleted:
            {var} = {var}.where({cn}.deleted_at.is_(None))
        """,
        level=_T_METHOD,
    )


def _repo_tenant_filter(domain: DomainSpec, cn: str, var: str = "stmt") -> str:
    if not domain.tenant_scoped:
        return ""
    return _snippet(
        f"""
        if tenant_id is not None:
            {var} = {var}.where({cn}.tenant_id == tenant_id)
        """,
        level=_T_METHOD,
    )


def _repo_create_tenant_body(domain: DomainSpec) -> str:
    if domain.tenant_scoped:
        return _snippet(
            """
            if tenant_id is None:
                raise ValueError('tenant_id required')
            payload['tenant_id'] = tenant_id
            """,
            level=_T_METHOD,
        )
    return _snippet("pass  # not tenant-scoped", level=_T_METHOD)


def _repo_soft_delete_body(domain: DomainSpec) -> str:
    if domain.soft_delete:
        return _snippet("entity.deleted_at = datetime.now(timezone.utc)", level=_T_METHOD)
    return _snippet("await self._session.delete(entity)", level=_T_METHOD)


def _repo_restore_body(domain: DomainSpec) -> str:
    if domain.soft_delete:
        return _snippet(
            f"""
            if entity.deleted_at is None:
                return entity
            entity.deleted_at = None
            await self._session.flush()
            await self._session.refresh(entity)
            logger.info('{domain.snake}.restored', entity_id=str(entity.id))
            return entity
            """,
            level=_T_METHOD,
        )
    return _snippet("return entity  # hard-delete domain has no restore", level=_T_METHOD)


def _repo_list_deleted_body(domain: DomainSpec) -> str:
    if domain.soft_delete:
        return _snippet(
            "return await self.list(tenant_id=tenant_id, page=page, page_size=page_size, include_deleted=True)",
            level=_T_METHOD,
        )
    return _snippet("return [], 0", level=_T_METHOD)


def _repository_filter_helpers(domain: DomainSpec) -> tuple[list[str], str, str, list[str]]:
    cn = domain.class_name
    filterable = [f for f in domain.fields if f.indexed][:6]
    string_search = [f.name for f in domain.fields if f.python_type == "str" and f.indexed][:2]
    order_fields = ["created_at", "updated_at"] + [f.name for f in domain.fields if f.indexed][:3]
    filter_apply = []
    for f in filterable:
        filter_apply.append(
            f'if filters.get("{f.name}") is not None:\n'
            f'    stmt = stmt.where({cn}.{f.name} == filters["{f.name}"])\n'
            f'    count_stmt = count_stmt.where({cn}.{f.name} == filters["{f.name}"])'
        )
    search_block = ""
    if string_search:
        conditions = " | ".join(f"{cn}.{name}.ilike(pattern)" for name in string_search)
        search_block = _snippet(
            f"""
            search = filters.get("search")
            if search:
                pattern = f"%{{search}}%"
                stmt = stmt.where(or_({conditions}))
                count_stmt = count_stmt.where(or_({conditions}))
            """,
            level=_T_METHOD,
        )
    order_block = _snippet(
        "\n".join(f'"{field}": {cn}.{field},' for field in order_fields),
        level=_T_METHOD,
    )
    return filter_apply, search_block, order_block, [f.name for f in filterable]


def _method_http_status(method: MethodSpec) -> int:
    if method.http_verb == "DELETE":
        return 204
    if method.name in ("create", "clone", "merge_into"):
        return 201
    if method.http_verb == "POST" and method.returns != "None":
        return 200
    return 200


def generate_repository(domain: DomainSpec) -> str:
    cn = domain.class_name
    filterable = [f.name for f in domain.fields if f.indexed][:6]
    filter_params = ", ".join(
        f"{fname}: {_pydantic_type(next(x for x in domain.fields if x.name == fname))} | None = None"
        for fname in filterable
    )
    list_filter_line = f"                {filter_params},\n" if filter_params else ""
    filter_dict_entries = ", ".join(f'"{fname}": {fname}' for fname in filterable)
    filter_dict_body = f"{filter_dict_entries},\n                    " if filter_dict_entries else ""
    filter_apply, search_block, order_block, _ = _repository_filter_helpers(domain)
    filter_block = (
        _snippet("\n\n".join(filter_apply), level=_T_METHOD)
        if filter_apply
        else _snippet("pass", level=_T_METHOD)
    )
    base_select_body = _repo_base_select_body(domain, cn)
    apply_tenant_body = _repo_apply_tenant_body(domain, cn)
    exists_deleted = _repo_deleted_filter(domain, cn, "stmt")
    exists_tenant = _repo_tenant_filter(domain, cn, "stmt")
    count_deleted = _repo_deleted_filter(domain, cn, "count_stmt")
    list_count_deleted = _repo_deleted_filter(domain, cn, "count_stmt")
    create_tenant_body = _repo_create_tenant_body(domain)
    soft_delete_body = _repo_soft_delete_body(domain)
    restore_body = _repo_restore_body(domain)
    list_deleted_body = _repo_list_deleted_body(domain)

    return f'''\
        """Data access layer for {domain.title}."""

        from __future__ import annotations

        from datetime import datetime, timezone
        from typing import Any
        from uuid import UUID

        import structlog
        from sqlalchemy import Select, func, or_, select
        from sqlalchemy.ext.asyncio import AsyncSession

        from app.domains.{domain.snake}.models import {cn}
        from app.domains.{domain.snake}.schemas import {cn}Create, {cn}Update

        logger = structlog.get_logger(__name__)


        class {cn}Repository:
            """Persistence operations for {domain.plural} with filter, ordering, and soft-delete support."""

            _ORDERABLE = {{
{order_block}
            }}

            def __init__(self, session: AsyncSession) -> None:
                self._session = session

            def _base_select(self, *, include_deleted: bool = False) -> Select[tuple[{cn}]]:
                stmt: Select[tuple[{cn}]] = select({cn})
{base_select_body}
                return stmt

            def _apply_tenant(self, stmt: Select[tuple[{cn}]], tenant_id: UUID | None) -> Select[tuple[{cn}]]:
{apply_tenant_body}
                return stmt

            def _apply_filters(
                self,
                stmt: Select[tuple[{cn}]],
                count_stmt: Select[tuple[int]],
                filters: dict[str, Any],
            ) -> tuple[Select[tuple[{cn}]], Select[tuple[int]]]:
{filter_block}
{search_block}
                return stmt, count_stmt

            def _apply_ordering(
                self,
                stmt: Select[tuple[{cn}]],
                *,
                order_by: str = "created_at",
                order_dir: str = "desc",
            ) -> Select[tuple[{cn}]]:
                column = self._ORDERABLE.get(order_by, {cn}.created_at)
                if order_dir.lower() == "asc":
                    return stmt.order_by(column.asc())
                return stmt.order_by(column.desc())

            async def get_by_id(
                self,
                entity_id: UUID,
                *,
                tenant_id: UUID | None = None,
                include_deleted: bool = False,
            ) -> {cn} | None:
                stmt = self._base_select(include_deleted=include_deleted).where({cn}.id == entity_id)
                stmt = self._apply_tenant(stmt, tenant_id)
                result = await self._session.execute(stmt)
                row = result.scalar_one_or_none()
                logger.debug("{domain.snake}.get_by_id", entity_id=str(entity_id), found=row is not None)
                return row

            async def exists(
                self,
                entity_id: UUID,
                *,
                tenant_id: UUID | None = None,
                include_deleted: bool = False,
            ) -> bool:
                stmt = select(func.count()).select_from({cn}).where({cn}.id == entity_id)
{exists_deleted}
{exists_tenant}
                count = (await self._session.execute(stmt)).scalar_one()
                return int(count) > 0

            async def count(
                self,
                *,
                tenant_id: UUID | None = None,
                include_deleted: bool = False,
                **filters: Any,
            ) -> int:
                count_stmt = select(func.count()).select_from({cn})
{count_deleted}
                count_stmt = self._apply_tenant(count_stmt, tenant_id)
                stmt = select({cn})
                stmt = self._apply_tenant(stmt, tenant_id)
                _, count_stmt = self._apply_filters(stmt, count_stmt, filters)
                total = (await self._session.execute(count_stmt)).scalar_one()
                return int(total)

            async def list(
                self,
                *,
                tenant_id: UUID | None = None,
                page: int = 1,
                page_size: int = 50,
                order_by: str = "created_at",
                order_dir: str = "desc",
                include_deleted: bool = False,
{list_filter_line}                search: str | None = None,
            ) -> tuple[list[{cn}], int]:
                filters: dict[str, Any] = {{
                    {filter_dict_body}"search": search,
                }}
                stmt = self._base_select(include_deleted=include_deleted)
                count_stmt = select(func.count()).select_from({cn})
{list_count_deleted}
                stmt = self._apply_tenant(stmt, tenant_id)
                count_stmt = self._apply_tenant(count_stmt, tenant_id)
                stmt, count_stmt = self._apply_filters(stmt, count_stmt, filters)
                total = (await self._session.execute(count_stmt)).scalar_one()
                stmt = self._apply_ordering(stmt, order_by=order_by, order_dir=order_dir)
                stmt = stmt.offset((page - 1) * page_size).limit(page_size)
                rows = (await self._session.execute(stmt)).scalars().all()
                logger.debug(
                    "{domain.snake}.list",
                    count=len(rows),
                    total=int(total),
                    page=page,
                    order_by=order_by,
                )
                return list(rows), int(total)

            async def list_deleted(
                self,
                *,
                tenant_id: UUID | None = None,
                page: int = 1,
                page_size: int = 50,
            ) -> tuple[list[{cn}], int]:
{list_deleted_body}

            async def create(self, data: {cn}Create, *, tenant_id: UUID | None = None) -> {cn}:
                payload = data.model_dump(exclude_unset=True)
{create_tenant_body}
                entity = {cn}(**payload)
                self._session.add(entity)
                await self._session.flush()
                await self._session.refresh(entity)
                logger.info("{domain.snake}.created", entity_id=str(entity.id), tenant_id=str(tenant_id) if tenant_id else None)
                return entity

            async def update(self, entity: {cn}, data: {cn}Update) -> {cn}:
                changes = data.model_dump(exclude_unset=True)
                for key, value in changes.items():
                    setattr(entity, key, value)
                await self._session.flush()
                await self._session.refresh(entity)
                logger.info("{domain.snake}.updated", entity_id=str(entity.id), fields=sorted(changes))
                return entity

            async def soft_delete(self, entity: {cn}) -> None:
{soft_delete_body}
                await self._session.flush()
                logger.info("{domain.snake}.deleted", entity_id=str(entity.id))

            async def restore(self, entity: {cn}) -> {cn}:
{restore_body}
        '''


def _generate_method_body(domain: DomainSpec, method: MethodSpec) -> str:
    cn = domain.class_name
    name = method.name
    bodies: dict[str, str] = {
        "activate": f"""if entity.is_active:
    raise {cn}ConflictError("Tenant is already active")
entity.is_active = True
logger.info("{domain.snake}.activate", entity_id=str(entity.id))""",
        "deactivate": f"""if not entity.is_active:
    raise {cn}ConflictError("Tenant is already inactive")
entity.is_active = False
logger.info("{domain.snake}.deactivate", entity_id=str(entity.id))""",
        "submit": f"""if entity.status != "draft":
    raise {cn}ValidationError("Only draft work orders may be submitted")
entity.status = "submitted"
logger.info("{domain.snake}.submit", entity_id=str(entity.id))""",
        "complete": f"""if entity.status not in {{"in_progress", "submitted"}}:
    raise {cn}ValidationError("Work order cannot be completed from status {{entity.status}}")
entity.status = "completed"
if notes:
    entity.completion_notes = notes
logger.info("{domain.snake}.complete", entity_id=str(entity.id))""",
        "cancel": f"""if entity.status == "completed":
    raise {cn}ConflictError("Completed work orders cannot be cancelled")
entity.status = "cancelled"
logger.info("{domain.snake}.cancel", entity_id=str(entity.id), reason=reason)""",
        "finalize": f"""if entity.status != "draft":
    raise {cn}ValidationError("Only draft invoices may be finalized")
entity.status = "finalized"
logger.info("{domain.snake}.finalize", entity_id=str(entity.id))""",
        "assign_technician": f"""self._set_status(entity, "assigned", action="assign_technician")
entity.assigned_technician_id = technician_id
logger.info("{domain.snake}.assign_technician", entity_id=str(entity.id), technician_id=str(technician_id))""",
        "start": f"""self._set_status(entity, "in_progress", action="start")
logger.info("{domain.snake}.start", entity_id=str(entity.id))""",
        "set_status": f"""if not status:
    raise {cn}ValidationError("status is required")
self._set_status(entity, status, action="set_status")
logger.info("{domain.snake}.set_status", entity_id=str(entity.id), status=status)""",
        "approve": f"""self._set_status(entity, "approved", action="approve")
logger.info("{domain.snake}.approve", entity_id=str(entity.id))""",
        "fulfill": f"""if entity.status != "approved":
    raise {cn}ValidationError("Only approved requests may be fulfilled")
entity.status = "fulfilled"
logger.info("{domain.snake}.fulfill", entity_id=str(entity.id))""",
        "reject": f"""if entity.status not in {{"pending", "approved"}}:
    raise {cn}ValidationError("Request cannot be rejected in current state")
entity.status = "rejected"
logger.info("{domain.snake}.reject", entity_id=str(entity.id), reason=reason)""",
        "acknowledge": f"""entity.acknowledged = True
logger.info("{domain.snake}.acknowledge", entity_id=str(entity.id))""",
        "escalate": f"""entity.escalation_level += 1
logger.info("{domain.snake}.escalate", entity_id=str(entity.id), level=entity.escalation_level)""",
        "mark_sent": f"""from datetime import datetime, timezone
entity.status = "sent"
entity.sent_at = datetime.now(timezone.utc)
logger.info("{domain.snake}.mark_sent", entity_id=str(entity.id))""",
        "mark_failed": f"""entity.status = "failed"
logger.info("{domain.snake}.mark_failed", entity_id=str(entity.id), error=error)""",
        "retry": f"""if entity.status != "failed":
    raise {cn}ValidationError("Only failed notifications may be retried")
entity.status = "pending"
logger.info("{domain.snake}.retry", entity_id=str(entity.id))""",
    }
    template = bodies.get(name)
    if template is None:
        template = (
            f'logger.info("{domain.snake}.{name}.start", entity_id=str(entity.id))\n'
            f"# {method.description}\n"
            f'logger.info("{domain.snake}.{name}.complete", entity_id=str(entity.id))'
        )
    return textwrap.dedent(template).strip("\n")


def _embed_method_body(body: str) -> str:
    return "\n".join(f"    {line}" if line else line for line in body.splitlines())


def generate_service(domain: DomainSpec) -> str:
    cn = domain.class_name
    method_defs = []
    for m in domain.methods:
        sig_params = ", ".join(f"{n}: {_map_param_type(t)}" for n, t in m.params)
        if sig_params:
            sig_params = ", " + sig_params

        body = _embed_method_body(_generate_method_body(domain, m))
        ret = f" -> {m.returns}" if m.returns != "None" else ""
        method_defs.append(
            _snippet(
                f"""
async def {m.name}(self, entity_id: UUID, tenant_id: UUID | None{sig_params}){ret}:
    \"\"\"{m.description}\"\"\"
    entity = await self._require_entity(entity_id, tenant_id=tenant_id)
{body}
    await self._repo._session.flush()
    await self._repo._session.refresh(entity)
    return entity
                """,
                level=_T_CLASS,
            )
        )

    methods_block = "\n\n".join(method_defs)

    validate_create = _service_create_validation(domain)
    validate_update = _service_update_validation(domain)
    status_block = _status_transition_block(domain)
    validate_tenant_body = _service_validate_tenant_body(domain, cn)

    return f'''\
        """Business logic for {domain.title}."""

        from __future__ import annotations

        from typing import Any
        from uuid import UUID

        import structlog

        from app.domains.{domain.snake}.exceptions import (
            {cn}ConflictError,
            {cn}NotFoundError,
            {cn}ValidationError,
        )
        from app.domains.{domain.snake}.models import {cn}
        from app.domains.{domain.snake}.repository import {cn}Repository
        from app.domains.{domain.snake}.schemas import {cn}Create, {cn}Read, {cn}Update

        logger = structlog.get_logger(__name__)


        class {cn}Service:
            """Orchestrates {domain.snake} use cases with validation, transitions, and auditing."""

            def __init__(self, repository: {cn}Repository) -> None:
                self._repo = repository

{status_block}

            async def _require_entity(
                self, entity_id: UUID, *, tenant_id: UUID | None = None
            ) -> {cn}:
                entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id)
                if entity is None:
                    logger.warning("{domain.snake}.not_found", entity_id=str(entity_id))
                    raise {cn}NotFoundError(entity_id)
                return entity

            def _validate_tenant(self, tenant_id: UUID | None) -> UUID:
{validate_tenant_body}

            async def get(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> {cn}Read:
                tenant_id = self._validate_tenant(tenant_id)
                entity = await self._require_entity(entity_id, tenant_id=tenant_id)
                logger.info("{domain.snake}.service.get", entity_id=str(entity_id))
                return {cn}Read.model_validate(entity)

            async def list(
                self,
                *,
                tenant_id: UUID | None = None,
                page: int = 1,
                page_size: int = 50,
                order_by: str = "created_at",
                order_dir: str = "desc",
                **filters: Any,
            ) -> tuple[list[{cn}Read], int]:
                tenant_id = self._validate_tenant(tenant_id)
                if page < 1:
                    raise {cn}ValidationError("Page must be >= 1")
                if page_size < 1 or page_size > 200:
                    raise {cn}ValidationError("Page size must be between 1 and 200")
                rows, total = await self._repo.list(
                    tenant_id=tenant_id,
                    page=page,
                    page_size=page_size,
                    order_by=order_by,
                    order_dir=order_dir,
                    **filters,
                )
                logger.info(
                    "{domain.snake}.service.list",
                    page=page,
                    page_size=page_size,
                    total=total,
                    returned=len(rows),
                )
                return [{cn}Read.model_validate(r) for r in rows], total

            async def count(self, *, tenant_id: UUID | None = None, **filters: Any) -> int:
                tenant_id = self._validate_tenant(tenant_id)
                return await self._repo.count(tenant_id=tenant_id, **filters)

            async def exists(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> bool:
                tenant_id = self._validate_tenant(tenant_id)
                return await self._repo.exists(entity_id, tenant_id=tenant_id)

            async def create(
                self, data: {cn}Create, *, tenant_id: UUID | None = None
            ) -> {cn}Read:
                tenant_id = self._validate_tenant(tenant_id)
                self._validate_create(data)
                entity = await self._repo.create(data, tenant_id=tenant_id)
                logger.info("{domain.snake}.service.create", entity_id=str(entity.id), tenant_id=str(tenant_id))
                return {cn}Read.model_validate(entity)

            async def update(
                self,
                entity_id: UUID,
                data: {cn}Update,
                *,
                tenant_id: UUID | None = None,
            ) -> {cn}Read:
                tenant_id = self._validate_tenant(tenant_id)
                entity = await self._require_entity(entity_id, tenant_id=tenant_id)
                self._validate_update(entity, data)
                updated = await self._repo.update(entity, data)
                logger.info("{domain.snake}.service.update", entity_id=str(entity_id))
                return {cn}Read.model_validate(updated)

            async def delete(
                self, entity_id: UUID, *, tenant_id: UUID | None = None
            ) -> None:
                tenant_id = self._validate_tenant(tenant_id)
                entity = await self._require_entity(entity_id, tenant_id=tenant_id)
                await self._repo.soft_delete(entity)
                logger.info("{domain.snake}.service.delete", entity_id=str(entity_id))

            async def restore(
                self, entity_id: UUID, *, tenant_id: UUID | None = None
            ) -> {cn}Read:
                tenant_id = self._validate_tenant(tenant_id)
                entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id, include_deleted=True)
                if entity is None:
                    raise {cn}NotFoundError(entity_id)
                restored = await self._repo.restore(entity)
                logger.info("{domain.snake}.service.restore", entity_id=str(entity_id))
                return {cn}Read.model_validate(restored)

            def _validate_create(self, data: {cn}Create) -> None:
                """Domain-specific create validation for {domain.title}."""
{validate_create}

            def _validate_update(self, entity: {cn}, data: {cn}Update) -> None:
                """Domain-specific update validation for {domain.title}."""
{validate_update}

{methods_block}
        '''


def _router_extra_route(domain: DomainSpec, m: MethodSpec) -> str:
    cn = domain.class_name
    params_sig = ", ".join(f"{n}=payload.{n}" for n, _ in m.params)
    verb = m.http_verb.lower()
    path = m.path_suffix or f"/{m.name.replace('_', '-')}"
    status_code = _method_http_status(m)
    status_arg = f", status_code=status.HTTP_{status_code}" if status_code != 200 else ""
    req_cls = f"{cn}{_method_class_suffix(m.name)}Request" if m.params else None
    decorator = f'@router.{verb}("/{{entity_id}}{path}", response_model={cn}Read{status_arg})'
    payload_param = f"            payload: {req_cls},\n" if req_cls else ""
    call_args = f"entity_id, tenant_id{', ' + params_sig if params_sig else ''}"
    return _snippet(
        f"""
        {decorator}
        async def {m.name}(
            entity_id: UUID,
{payload_param}            service: {cn}Service = Depends(get_{domain.snake}_service),
            tenant_id: UUID = Depends(get_tenant_id),
        ) -> {cn}Read:
            \"\"\"{m.description}\"\"\"
            result = await service.{m.name}({call_args})
            if hasattr(result, "__table__"):
                return {cn}Read.model_validate(result)
            return result
        """,
        level=_T_BASE,
    )


def generate_router(domain: DomainSpec) -> str:
    cn = domain.class_name
    route_prefix = f"/{domain.plural.replace('_', '-')}"
    filterable = [f for f in domain.fields if f.indexed][:4]
    filter_query_params = ""
    if filterable:
        filter_query_params = _snippet(
            "\n".join(
                f"{f.name}: {_pydantic_type(f)} | None = Query(default=None),"
                for f in filterable
            ),
            level=_T_CLASS,
        )
        filter_query_params = f"{filter_query_params}\n"
    filter_pass = ", ".join(f"{f.name}={f.name}" for f in filterable)
    list_filter_pass = f"                {filter_pass},\n" if filter_pass else ""

    extra_block = "\n\n".join(_router_extra_route(domain, m) for m in domain.methods)
    restore_route = ""
    if domain.soft_delete:
        restore_route = _snippet(
            f"""
            @router.post("/{{entity_id}}/restore", response_model={cn}Read)
            async def restore_{domain.snake}(
                entity_id: UUID,
                service: {cn}Service = Depends(get_{domain.snake}_service),
                tenant_id: UUID = Depends(get_tenant_id),
            ) -> {cn}Read:
                return await service.restore(entity_id, tenant_id=tenant_id)
            """,
            level=_T_BASE,
        )

    return f'''\
        """FastAPI routes for {domain.title}."""

        from __future__ import annotations

        from uuid import UUID

        from fastapi import APIRouter, Depends, Query, status

        from app.deps import get_db_session, get_tenant_id
        from app.domains.{domain.snake}.repository import {cn}Repository
        from app.domains.{domain.snake}.schemas import (
            {cn}Create,
            {cn}ListResponse,
            {cn}Read,
            {cn}Update,
        )
        from app.domains.{domain.snake}.service import {cn}Service

        router = APIRouter(prefix="{route_prefix}", tags=["{domain.title}"])


        def get_{domain.snake}_service(session=Depends(get_db_session)) -> {cn}Service:
            return {cn}Service({cn}Repository(session))


        @router.get("", response_model={cn}ListResponse)
        async def list_{domain.plural}(
            page: int = Query(1, ge=1),
            page_size: int = Query(50, ge=1, le=200),
            search: str | None = Query(default=None, min_length=1, max_length=200),
            order_by: str = Query(default="created_at"),
            order_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
{filter_query_params}            service: {cn}Service = Depends(get_{domain.snake}_service),
            tenant_id: UUID = Depends(get_tenant_id),
        ) -> {cn}ListResponse:
            items, total = await service.list(
                tenant_id=tenant_id,
                page=page,
                page_size=page_size,
                search=search,
                order_by=order_by,
                order_dir=order_dir,
{list_filter_pass}            )
            return {cn}ListResponse.from_page(items, total, page, page_size)


        @router.get("/count")
        async def count_{domain.plural}(
            service: {cn}Service = Depends(get_{domain.snake}_service),
            tenant_id: UUID = Depends(get_tenant_id),
        ) -> dict[str, int]:
            total = await service.count(tenant_id=tenant_id)
            return {{"total": total}}


        @router.post("", response_model={cn}Read, status_code=status.HTTP_201_CREATED)
        async def create_{domain.snake}(
            payload: {cn}Create,
            service: {cn}Service = Depends(get_{domain.snake}_service),
            tenant_id: UUID = Depends(get_tenant_id),
        ) -> {cn}Read:
            return await service.create(payload, tenant_id=tenant_id)


        @router.get("/{{entity_id}}", response_model={cn}Read)
        async def get_{domain.snake}(
            entity_id: UUID,
            service: {cn}Service = Depends(get_{domain.snake}_service),
            tenant_id: UUID = Depends(get_tenant_id),
        ) -> {cn}Read:
            return await service.get(entity_id, tenant_id=tenant_id)


        @router.patch("/{{entity_id}}", response_model={cn}Read)
        async def update_{domain.snake}(
            entity_id: UUID,
            payload: {cn}Update,
            service: {cn}Service = Depends(get_{domain.snake}_service),
            tenant_id: UUID = Depends(get_tenant_id),
        ) -> {cn}Read:
            return await service.update(entity_id, payload, tenant_id=tenant_id)


        @router.delete("/{{entity_id}}", status_code=status.HTTP_204_NO_CONTENT)
        async def delete_{domain.snake}(
            entity_id: UUID,
            service: {cn}Service = Depends(get_{domain.snake}_service),
            tenant_id: UUID = Depends(get_tenant_id),
        ) -> None:
            await service.delete(entity_id, tenant_id=tenant_id)
{restore_route}
{extra_block}
        '''


def generate_domain_init(domain: DomainSpec) -> str:
    cn = domain.class_name
    return f'"""{domain.title} domain package."""\n\nfrom app.domains.{domain.snake}.models import {cn}\n\n__all__ = ["{cn}"]\n'


def generate_all_domain_files(domain: DomainSpec) -> dict[str, str]:
    """Return mapping of filename -> source for a single domain."""
    return {
        "__init__.py": generate_domain_init(domain),
        "models.py": generate_models(domain),
        "schemas.py": generate_schemas(domain),
        "repository.py": generate_repository(domain),
        "service.py": generate_service(domain),
        "router.py": generate_router(domain),
        "exceptions.py": generate_exceptions(domain),
    }
