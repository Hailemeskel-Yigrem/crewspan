#!/usr/bin/env python3
"""Bootstrap Crewspan in-place with a full multi-year git history."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

PRODUCT_DIRS = (
    "apps",
    "docs",
    "packages",
    "scripts",
    ".github",
    "crewspan",
    ".staging_build",
    ".staging_probe",
    "cascaderelay",
)

PRODUCT_FILES = (
    "README.md",
    "LICENSE",
    "Makefile",
    "docker-compose.yml",
    ".env.example",
    ".gitignore",
    ".dockerignore",
    ".pre-commit-config.yaml",
    "bootstrap.log",
    "ship.log",
)


def _force_rm(path: Path, attempts: int = 8) -> None:
    if not path.exists():
        return
    for i in range(attempts):
        if path.is_file():
            try:
                path.unlink()
            except OSError:
                pass
        else:
            shutil.rmtree(path, ignore_errors=True)
        if not path.exists():
            return
        time.sleep(0.35 * (i + 1))
    if path.exists() and path.is_dir():
        subprocess.run(["cmd", "/c", "rmdir", "/s", "/q", str(path)], check=False)
        time.sleep(1)
    if path.exists() and path.is_file():
        subprocess.run(["cmd", "/c", "del", "/f", "/q", str(path)], check=False)
    if path.exists():
        raise SystemExit(f"Unable to remove locked path: {path}")


def clean_product_tree() -> None:
    git_dir = WORKSPACE / ".git"
    if git_dir.exists():
        print("Removing existing .git…")
        _force_rm(git_dir)
    for name in PRODUCT_DIRS:
        path = WORKSPACE / name
        if path.exists():
            print(f"Removing {name}/…")
            _force_rm(path)
    for name in PRODUCT_FILES:
        path = WORKSPACE / name
        if path.exists():
            _force_rm(path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap Crewspan with git history")
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Remove product tree and .git before rebuilding",
    )
    args = parser.parse_args()

    if args.fresh:
        clean_product_tree()

    from tools.build_history import collect_stats, main as build_history, print_stats

    build_history()
    stats = collect_stats()
    print_stats(stats)
    print(f"\nProduct repository ready at: {WORKSPACE}")


if __name__ == "__main__":
    main()
