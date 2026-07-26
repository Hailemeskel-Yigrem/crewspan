from pathlib import Path

root = Path("apps/api")
n = 0
for path in root.rglob("*.py"):
    text = path.read_text(encoding="utf-8")
    if "from app.db import Base" in text:
        path.write_text(
            text.replace("from app.db import Base", "from app.base import Base"),
            encoding="utf-8",
            newline="\n",
        )
        n += 1
        print(path)

for path in Path("apps/api/app/domains").glob("*/__init__.py"):
    text = path.read_text(encoding="utf-8")
    if "from app.domains." in text and ".models import" in text:
        name = path.parent.name
        path.write_text(f'"""{name} domain package."""\n', encoding="utf-8", newline="\n")
        print("init", path)

env = Path("apps/api/alembic/env.py")
text = env.read_text(encoding="utf-8")
if "from app.db import Base" in text:
    text = text.replace("from app.db import Base", "from app.base import Base")
# Ensure models are imported for metadata
marker = "from app.base import Base\n"
if "import app.domains" not in text and marker in text:
    imports = [
        "from app.domains.tenant import models as tenant_models  # noqa: F401",
        "from app.domains.user import models as user_models  # noqa: F401",
        "from app.domains.role import models as role_models  # noqa: F401",
        "from app.domains.customer import models as customer_models  # noqa: F401",
        "from app.domains.customer_site import models as customer_site_models  # noqa: F401",
        "from app.domains.contact import models as contact_models  # noqa: F401",
        "from app.domains.work_order import models as work_order_models  # noqa: F401",
        "from app.domains.work_order_task import models as work_order_task_models  # noqa: F401",
        "from app.domains.technician import models as technician_models  # noqa: F401",
        "from app.domains.technician_skill import models as technician_skill_models  # noqa: F401",
        "from app.domains.schedule import models as schedule_models  # noqa: F401",
        "from app.domains.dispatch import models as dispatch_models  # noqa: F401",
        "from app.domains.inventory_item import models as inventory_item_models  # noqa: F401",
        "from app.domains.inventory_location import models as inventory_location_models  # noqa: F401",
        "from app.domains.stock_movement import models as stock_movement_models  # noqa: F401",
        "from app.domains.parts_request import models as parts_request_models  # noqa: F401",
        "from app.domains.invoice import models as invoice_models  # noqa: F401",
        "from app.domains.invoice_line_item import models as invoice_line_item_models  # noqa: F401",
        "from app.domains.payment import models as payment_models  # noqa: F401",
        "from app.domains.sla_policy import models as sla_policy_models  # noqa: F401",
        "from app.domains.sla_breach import models as sla_breach_models  # noqa: F401",
        "from app.domains.service_contract import models as service_contract_models  # noqa: F401",
        "from app.domains.equipment import models as equipment_models  # noqa: F401",
        "from app.domains.notification import models as notification_models  # noqa: F401",
        "from app.domains.webhook import models as webhook_models  # noqa: F401",
        "from app.domains.audit_log import models as audit_log_models  # noqa: F401",
    ]
    text = text.replace(marker, marker + "\n".join(imports) + "\n")
env.write_text(text, encoding="utf-8", newline="\n")
print("updated models", n)
