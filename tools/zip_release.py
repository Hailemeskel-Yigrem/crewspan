#!/usr/bin/env python3
"""Zip this working tree (including .git) as Crewspan. Does not create a git commit."""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT.parent / "Crewspan-shareable.zip"

SKIP_DIR_NAMES = {
    ".ruff_cache",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    ".venv",
    ".staging_build",
}
SKIP_SUFFIXES = {".pyc", ".zip", ".log"}


def zip_crewspan(output: Path) -> Path:
    if not (ROOT / ".git").exists():
        raise SystemExit(f"No git repository at {ROOT}.")

    output = output.resolve()
    if output.exists():
        output.unlink()

    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in ROOT.rglob("*"):
            if not path.is_file():
                continue
            if any(part in SKIP_DIR_NAMES for part in path.parts):
                continue
            if path.suffix.lower() in SKIP_SUFFIXES:
                continue
            if path.name.startswith("Crewspan-") and path.suffix == ".zip":
                continue
            arcname = Path("Crewspan") / path.relative_to(ROOT)
            zf.write(path, arcname.as_posix())

    size_mb = output.stat().st_size / (1024 * 1024)
    print(f"Created {output} ({size_mb:.2f} MiB)")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Zip Crewspan including .git")
    parser.add_argument("-o", "--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    zip_crewspan(args.output)


if __name__ == "__main__":
    main()
