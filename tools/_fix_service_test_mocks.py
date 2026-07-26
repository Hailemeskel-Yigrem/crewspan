"""Patch service unit-test mocks with typed entity attributes (uncommitted)."""

from __future__ import annotations

from pathlib import Path

from tools.codegen.domains import DOMAINS


def _field_assignment(field) -> str:
    name = field.name
    ftype = field.python_type.lower()
    if "uuid" in ftype:
        return f"    entity.{name} = uuid4()\n"
    if "bool" in ftype:
        return f"    entity.{name} = True\n"
    if ftype.startswith("int") or ftype == "int":
        return f"    entity.{name} = 1\n"
    if "decimal" in ftype or "float" in ftype:
        return f"    entity.{name} = Decimal('10.00')\n"
    if "datetime" in ftype:
        return f"    entity.{name} = datetime.now(timezone.utc)\n"
    if ftype == "date" or ftype.startswith("date |") or "date |" in ftype:
        return f"    entity.{name} = date.today()\n"
    if name == "status":
        return f'    entity.{name} = "draft"\n'
    if name == "email":
        return f'    entity.{name} = "ops@example.com"\n'
    return f'    entity.{name} = "sample-{name}"\n'


def main() -> None:
    for domain in DOMAINS:
        path = Path(f"apps/api/tests/unit/test_{domain.snake}_service.py")
        if not path.exists():
            continue
        assigns = "".join(_field_assignment(f) for f in domain.fields)
        assigns += "    entity.created_at = datetime.now(timezone.utc)\n"
        assigns += "    entity.updated_at = datetime.now(timezone.utc)\n"
        assigns += "    entity.deleted_at = None\n"

        fixture = f'''@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    entity = MagicMock()
    entity.id = uuid4()
    entity.tenant_id = uuid4()
{assigns}    repo.get_by_id.return_value = entity
    repo.list.return_value = ([entity], 1)
    repo.count.return_value = 1
    repo.exists.return_value = True
    repo.create.return_value = entity
    repo.update.return_value = entity
    return repo
'''
        text = path.read_text(encoding="utf-8")
        # Ensure imports
        if "from datetime import" not in text:
            text = text.replace(
                "from decimal import Decimal\n",
                "from datetime import date, datetime, timezone\nfrom decimal import Decimal\n",
                1,
            )
        elif "timezone" not in text:
            text = text.replace("from datetime import ", "from datetime import timezone, ", 1)

        start = text.find("@pytest.fixture\ndef mock_repo():")
        if start < 0:
            print("no fixture", path)
            continue
        end = text.find("@pytest.fixture\ndef service(", start)
        if end < 0:
            print("no service fixture", path)
            continue
        text = text[:start] + fixture + "\n\n" + text[end:]
        # Fix get() kwarg order issues: service.get(tenant_id=..., entity_id=...) -> positional entity_id
        text = text.replace(
            "await service.get(tenant_id=uuid4(), entity_id=uuid4())",
            "await service.get(uuid4(), tenant_id=uuid4())",
        )
        path.write_text(text, encoding="utf-8", newline="\n")
        print("patched", path)


if __name__ == "__main__":
    main()
