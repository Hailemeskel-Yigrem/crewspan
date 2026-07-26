import ast
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
count = subprocess.check_output(["git", "rev-list", "--count", "HEAD"], cwd=root, text=True).strip()
head = subprocess.check_output(["git", "log", "-1", "--oneline"], cwd=root, text=True).strip()
print("commits", count)
print("head", head)

svc = root / "apps/api/app/domains/work_order_task/service.py"
ast.parse(svc.read_text(encoding="utf-8"))
print("service.py OK")

errors = 0
for path in (root / "apps").rglob("*.py"):
    if "__pycache__" in path.parts:
        continue
    try:
        ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        errors += 1
print("syntax_errors", errors)
