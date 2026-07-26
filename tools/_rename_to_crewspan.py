"""Force working tree branding to Crewspan."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".ruff_cache", "__pycache__", "node_modules", ".venv", ".staging_build"}
SKIP_SUFFIX = {".zip", ".pyc", ".png", ".jpg", ".ico", ".log"}

REPLACEMENTS = (
    ("fieldspan_common", "crewspan_common"),
    ("fieldspan_sdk", "crewspan_sdk"),
    ("crewline_common", "crewspan_common"),
    ("crewline_sdk", "crewspan_sdk"),
    ("relayops_common", "crewspan_common"),
    ("relayops_sdk", "crewspan_sdk"),
    ("Fieldspan", "Crewspan"),
    ("FIELDSPAN", "CREWSPAN"),
    ("fieldspan", "crewspan"),
    ("Crewline", "Crewspan"),
    ("CREWLINE", "CREWSPAN"),
    ("crewline", "crewspan"),
    ("RelayOps", "Crewspan"),
    ("RELAYOPS", "CREWSPAN"),
    ("relayops", "crewspan"),
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
        if path.name.startswith("_rename_to_"):
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
        ("fieldspan_common", "crewspan_common"),
        ("crewline_common", "crewspan_common"),
        ("relayops_common", "crewspan_common"),
        ("fieldspan_sdk", "crewspan_sdk"),
        ("crewline_sdk", "crewspan_sdk"),
        ("relayops_sdk", "crewspan_sdk"),
    ):
        base = ROOT / ("packages/common/src" if "common" in src_name else "packages/sdk/src")
        src, dest = base / src_name, base / dest_name
        if src.exists() and not dest.exists():
            src.rename(dest)
            print(f"renamed-dir {src.relative_to(ROOT)} -> {dest.relative_to(ROOT)}")
        elif src.exists() and dest.exists() and src != dest:
            shutil.rmtree(src)
            print(f"removed-dup {src.relative_to(ROOT)}")

    print(f"done: {changed} files updated to Crewspan")


if __name__ == "__main__":
    main()
