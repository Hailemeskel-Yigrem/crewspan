"""Force this working tree to Fieldspan branding. Do NOT commit. Do NOT rename to Fieldspan/Fieldspan."""

from __future__ import annotations

from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".ruff_cache", "__pycache__", "node_modules", ".venv", ".staging_build"}
SKIP_SUFFIX = {".zip", ".pyc", ".png", ".jpg", ".ico", ".log"}

REPLACEMENTS = (
    ("fieldspan_common", "fieldspan_common"),
    ("fieldspan_sdk", "fieldspan_sdk"),
    ("fieldspan_common", "fieldspan_common"),
    ("fieldspan_sdk", "fieldspan_sdk"),
    ("fieldspan_common", "fieldspan_common"),
    ("fieldspan_sdk", "fieldspan_sdk"),
    ("Fieldspan", "Fieldspan"),
    ("FIELDSPAN", "FIELDSPAN"),
    ("fieldspan", "fieldspan"),
    ("Fieldspan", "Fieldspan"),
    ("FIELDSPAN", "FIELDSPAN"),
    ("fieldspan", "fieldspan"),
    ("Fieldspan", "Fieldspan"),
    ("FIELDSPAN", "FIELDSPAN"),
    ("fieldspan", "fieldspan"),
)


def main() -> None:
    changed = 0
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in SKIP_SUFFIX:
            continue
        if path.name.startswith("_rename_to_") and path.name != "_rename_to_fieldspan.py":
            continue
        if path.name == "_rename_to_fieldspan.py":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        updated = text
        for old, new in REPLACEMENTS:
            updated = updated.replace(old, new)
        if updated != text:
            path.write_text(updated, encoding="utf-8", newline="\n")
            changed += 1
            print(path.relative_to(ROOT).as_posix())

    for src_name, dest_name in (
        ("fieldspan_common", "fieldspan_common"),
        ("fieldspan_common", "fieldspan_common"),
        ("fieldspan_common", "fieldspan_common"),
        ("fieldspan_sdk", "fieldspan_sdk"),
        ("fieldspan_sdk", "fieldspan_sdk"),
        ("fieldspan_sdk", "fieldspan_sdk"),
    ):
        if "common" in src_name:
            src = ROOT / "packages/common/src" / src_name
            dest = ROOT / "packages/common/src" / dest_name
        else:
            src = ROOT / "packages/sdk/src" / src_name
            dest = ROOT / "packages/sdk/src" / dest_name
        if src.exists() and not dest.exists():
            src.rename(dest)
            print(f"renamed-dir {src.relative_to(ROOT)} -> {dest.relative_to(ROOT)}")
        elif src.exists() and dest.exists() and src != dest:
            shutil.rmtree(src)
            print(f"removed-dup {src.relative_to(ROOT)}")

    print(f"done: {changed} files updated to Fieldspan (UNCOMMITTED)")


if __name__ == "__main__":
    main()
