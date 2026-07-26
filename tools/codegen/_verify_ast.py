"""Verify all generated Python files parse with ast.parse."""
from __future__ import annotations

import ast
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.codegen.generate_api import generate_api_tree
from tools.codegen.generate_expand import generate_expand_tree
from tools.codegen.generate_tests import generate_tests_tree

td = Path(tempfile.mkdtemp())
generate_api_tree(td)
generate_tests_tree(td)
generate_expand_tree(td)
errors: list[tuple[str, int, str]] = []
for p in td.rglob("*.py"):
    try:
        ast.parse(p.read_text(encoding="utf-8"))
    except SyntaxError as e:
        errors.append((str(p), e.lineno, e.msg))
print("errors", len(errors))
for err in errors[:30]:
    print(err)
assert not errors
