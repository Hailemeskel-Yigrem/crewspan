#!/usr/bin/env python3
"""Validate Fieldspan git history, scale, and authors before packaging."""

from __future__ import annotations

import subprocess
import sys
from collections import Counter
from datetime import date
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
PROJECT = WORKSPACE / "fieldspan"
sys.path.insert(0, str(WORKSPACE))

from tools.authors import AUTHORS

ALLOWED = {email.lower() for _, email in AUTHORS}
TODAY = date(2026, 7, 25)
START = date(2023, 3, 1)
END = date(2026, 3, 31)


def run(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=PROJECT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def main() -> None:
    if not (PROJECT / ".git").exists():
        raise SystemExit(f"Missing git repo at {PROJECT}")

    count = int(run("rev-list", "--count", "HEAD"))
    authors = run("log", "--format=%ae").splitlines()
    dates = run("log", "--format=%ad", "--date=short").splitlines()
    bad_authors = sorted({a for a in authors if a.lower() not in ALLOWED})
    parsed_dates = [date.fromisoformat(d) for d in dates if d]
    outside = [d for d in parsed_dates if d < START or d > END]
    today_commits = [d for d in parsed_dates if d == TODAY]

    py_files = list((PROJECT / "apps").rglob("*.py")) + list((PROJECT / "packages").rglob("*.py"))
    py_files = [p for p in py_files if "__pycache__" not in p.parts]
    ts_files = list((PROJECT / "apps" / "web").rglob("*.{ts,tsx}".replace("{ts,tsx}", "*")))
    # Glob separately for web sources
    web_files = [
        p
        for p in (PROJECT / "apps" / "web").rglob("*")
        if p.suffix in {".ts", ".tsx", ".js", ".jsx", ".css"} and "node_modules" not in p.parts
    ]
    test_files = list((PROJECT / "apps").rglob("test_*.py")) + list((PROJECT / "apps").rglob("*_test.py"))
    test_files += [p for p in (PROJECT / "apps" / "web").rglob("*.test.*") if "node_modules" not in p.parts]

    source_files = [
        p
        for p in PROJECT.rglob("*")
        if p.is_file()
        and ".git" not in p.parts
        and "node_modules" not in p.parts
        and "__pycache__" not in p.parts
        and ".pytest_cache" not in p.parts
        and p.suffix in {".py", ".ts", ".tsx", ".js", ".jsx", ".css", ".sql", ".yml", ".yaml", ".md", ".toml", ".json"}
    ]

    loc = 0
    for path in source_files:
        try:
            loc += sum(1 for _ in path.open(encoding="utf-8", errors="ignore"))
        except OSError:
            pass

    year_counts = Counter(d.year for d in parsed_dates)

    print(f"commits={count}")
    print(f"authors_ok={not bad_authors}")
    if bad_authors:
        print(f"bad_authors={bad_authors}")
    print(f"date_range={min(parsed_dates)} .. {max(parsed_dates)}")
    print(f"outside_range={len(outside)}")
    print(f"today_commits={len(today_commits)}")
    print(f"year_counts={dict(sorted(year_counts.items()))}")
    print(f"source_files~={len(source_files)}")
    print(f"python_files={len(py_files)}")
    print(f"web_files={len(web_files)}")
    print(f"test_files={len(test_files)}")
    print(f"approx_loc={loc}")
    print(f"unique_authors={len(set(authors))}")

    errors = []
    if bad_authors:
        errors.append("disallowed authors present")
    if outside:
        errors.append("commits outside intended timeline")
    if today_commits:
        errors.append("commits dated today")
    if count < 150:
        errors.append("commit count looks too low for 3-year history")
    if errors:
        print("VALIDATION_FAILED: " + "; ".join(errors))
        raise SystemExit(1)
    print("VALIDATION_OK")


if __name__ == "__main__":
    main()
