"""Replace Crewline/RelayOps branding with Fieldspan in this working tree. Do not commit."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SKIP_DIRS = {
    ".git",
    ".ruff_cache",
    "__pycache__",
    "node_modules",
    ".venv",
    ".staging_build",
    ".pytest_cache",
}

SKIP_FILES = {
    "Crewline-release.zip",
    "Crewline-shareable.zip",
    "RelayOps-release.zip",
    "RelayOps-shareable.zip",
    "Fieldspan-shareable.zip",
    "bootstrap.log",
    "ship.log",
    "_rename_to_crewline.py",
    "_rename_to_fieldspan.py",
}

# Order matters: longer / more specific tokens first.
REPLACEMENTS = (
    ("Crewline", "Fieldspan"),
    ("CREWLINE", "FIELDSPAN"),
    ("crewline", "fieldspan"),
    ("RelayOps", "Fieldspan"),
    ("RELAYOPS", "FIELDSPAN"),
    ("relayops", "fieldspan"),
)

DIR_RENAMES = (
    (ROOT / "packages" / "common" / "src" / "crewline_common", ROOT / "packages" / "common" / "src" / "fieldspan_common"),
    (ROOT / "packages" / "sdk" / "src" / "crewline_sdk", ROOT / "packages" / "sdk" / "src" / "fieldspan_sdk"),
    (ROOT / "packages" / "common" / "src" / "relayops_common", ROOT / "packages" / "common" / "src" / "fieldspan_common"),
    (ROOT / "packages" / "sdk" / "src" / "relayops_sdk", ROOT / "packages" / "sdk" / "src" / "fieldspan_sdk"),
)


def should_skip(path: Path) -> bool:
    if any(part in SKIP_DIRS for part in path.parts):
        return True
    if path.name in SKIP_FILES:
        return True
    if path.suffix.lower() in {".zip", ".pyc", ".png", ".jpg", ".ico", ".pack", ".idx", ".rev"}:
        return True
    return False


def rename_package_dirs() -> None:
    for src, dest in DIR_RENAMES:
        if src.exists() and not dest.exists():
            src.rename(dest)
            print(f"renamed {src.relative_to(ROOT)} -> {dest.relative_to(ROOT)}")
        elif src.exists() and dest.exists():
            # Merge by moving files then removing source.
            for item in src.rglob("*"):
                if item.is_file():
                    target = dest / item.relative_to(src)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(item), str(target))
            shutil.rmtree(src, ignore_errors=True)
            print(f"merged {src.relative_to(ROOT)} into {dest.relative_to(ROOT)}")


def main() -> None:
    rename_package_dirs()
    changed = 0
    for path in ROOT.rglob("*"):
        if not path.is_file() or should_skip(path):
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
            print(f"updated {path.relative_to(ROOT).as_posix()}")
    print(f"done: {changed} files updated (UNCOMMITTED)")


if __name__ == "__main__":
    main()
