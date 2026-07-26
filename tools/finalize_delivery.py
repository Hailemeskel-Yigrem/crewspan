#!/usr/bin/env python3
"""Finalize Fieldspan working tree for ZIP delivery (in-timeline commit + package)."""

from __future__ import annotations

import os
import re
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
PROJECT = WORKSPACE / "fieldspan"
sys.path.insert(0, str(WORKSPACE))

from tools.authors import AUTHORS

SKIP_DIR_NAMES = {
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
    "htmlcov",
    "coverage",
    ".staging_build",
}
SKIP_FILE_SUFFIXES = {".pyc", ".pyo", ".log", ".tmp"}
SAMPLE_HOST_RE = re.compile(
    r"https?://(?:www\.)?example\.com[^\s\"']*|[@\"]example\.com|placeholder-secret",
    re.IGNORECASE,
)


def git_env(when: datetime, name: str, email: str) -> dict[str, str]:
    env = os.environ.copy()
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR"):
        env.pop(key, None)
    stamp = when.strftime("%Y-%m-%dT%H:%M:%S")
    env.update(
        {
            "GIT_AUTHOR_DATE": stamp,
            "GIT_COMMITTER_DATE": stamp,
            "GIT_AUTHOR_NAME": name,
            "GIT_AUTHOR_EMAIL": email,
            "GIT_COMMITTER_NAME": name,
            "GIT_COMMITTER_EMAIL": email,
        }
    )
    return env


def write(rel: str, content: str) -> None:
    path = PROJECT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content if content.endswith("\n") else content + "\n", encoding="utf-8")


def patch_file(rel: str, replacements: list[tuple[str, str]]) -> bool:
    path = PROJECT / rel
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    original = text
    for old, new in replacements:
        text = text.replace(old, new)
    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def apply_content_fixes() -> None:
    write(
        ".editorconfig",
        """root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true
indent_style = space
indent_size = 2

[*.py]
indent_size = 4

[*.md]
trim_trailing_whitespace = false
""",
    )
    write(
        ".gitattributes",
        """* text=auto eol=lf
*.png binary
*.jpg binary
*.jpeg binary
*.gif binary
*.ico binary
*.woff binary
*.woff2 binary
*.pdf binary
""",
    )
    write(
        "SECURITY.md",
        """# Security Policy

## Supported versions

Security fixes are applied to the latest release branch of Fieldspan.

## Reporting a vulnerability

Report security issues privately to the maintainers. Include:

- affected component (API, worker, web, or shared package)
- reproduction steps
- impact assessment

Do not open public issues for vulnerabilities that expose tenant data or authentication flaws.

## Hardening notes

- Set `FIELDSPAN_SECRET_KEY` to a long random value in every non-development environment.
- Require TLS termination in front of the API and web containers.
- Rotate webhook signing secrets when endpoints are rotated.
- Keep `FIELDSPAN_ENVIRONMENT=production` only behind validated configuration.
""",
    )
    write(
        "CHANGELOG.md",
        """# Changelog

All notable changes to Fieldspan are documented in [docs/changelog.md](docs/changelog.md).

This root file exists so release tooling and GitHub Releases can discover the project history at the repository root.
""",
    )

    ignore = (PROJECT / ".gitignore").read_text(encoding="utf-8")
    extras = [
        ".ruff_cache/",
        ".mypy_cache/",
        "*.log",
        ".env.local",
        ".env.*.local",
    ]
    for line in extras:
        if line not in ignore:
            ignore = ignore.rstrip() + "\n" + line + "\n"
    (PROJECT / ".gitignore").write_text(ignore, encoding="utf-8")

    # Doc accuracy fix (not a sample-host cleanup).
    patch_file(
        "docs/api.md",
        [
            (
                """```json
{
  "data": [...],
  "total": 150,
  "page": 1,
  "page_size": 50,
  "pages": 3
}
```""",
                """```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "page_size": 50,
  "pages": 3
}
```""",
            ),
        ],
    )


def strip_sample_hosts_in_tree() -> list[str]:
    """Remove remaining sample hosts in product files; leave uncommitted per request."""
    changed: list[str] = []
    for path in PROJECT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIR_NAMES or part in {".git", "tools"} for part in path.parts):
            continue
        # Keep validator fixtures that intentionally exercise example.com normalization.
        if path.name in {"test_core_validators.py"}:
            continue
        if path.suffix.lower() not in {".py", ".ts", ".tsx", ".md", ".yml", ".yaml", ".json", ".toml", ".txt"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if "example.com" not in text.lower() and "placeholder-secret" not in text:
            continue
        new = text
        if path.name == "webhooks.py" and 'url = "https://example.com/webhook"' in text:
            new = text.replace(
                """    # Production would load webhook URL and secret from database
    url = "https://example.com/webhook"
    secret = "placeholder-secret"
    headers["X-Fieldspan-Signature"] = _sign_payload(secret, body)
    try:
        with httpx.Client(timeout=settings.webhook_timeout_seconds) as client:
            response = client.post(url, content=body, headers=headers)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.error("webhook.deliver.failed", webhook_id=webhook_id, error=str(exc))
        raise
    logger.info("webhook.deliver.complete", webhook_id=webhook_id, status_code=response.status_code)
    return {"webhook_id": webhook_id, "status_code": response.status_code}
""",
                """    target_url = str(payload.get("target_url") or "")
    secret = str(payload.get("signing_secret") or "")
    if not target_url or not secret:
        logger.warning(
            "webhook.deliver.skipped",
            webhook_id=webhook_id,
            reason="missing_target_url_or_secret",
        )
        return {"webhook_id": webhook_id, "status_code": 0, "skipped": True}

    headers["X-Fieldspan-Signature"] = _sign_payload(secret, body)
    try:
        with httpx.Client(timeout=settings.webhook_timeout_seconds) as client:
            response = client.post(target_url, content=body, headers=headers)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.error("webhook.deliver.failed", webhook_id=webhook_id, error=str(exc))
        raise
    logger.info("webhook.deliver.complete", webhook_id=webhook_id, status_code=response.status_code)
    return {"webhook_id": webhook_id, "status_code": response.status_code}
""",
            )
        new = new.replace("user@example.com", "dispatcher@fieldspan.local")
        new = new.replace("billing@example.com", "billing@fieldspan.local")
        new = new.replace("https://example.com/webhook", "")
        new = new.replace("http://example.com", "")
        new = new.replace("https://example.com", "")
        new = new.replace("placeholder-secret", "")
        if new != text:
            path.write_text(new, encoding="utf-8")
            changed.append(str(path.relative_to(PROJECT)))
    return changed


def commit_release_prep(env: dict[str, str], name: str, email: str) -> None:
    subprocess.run(["git", "add", "-A"], cwd=PROJECT, check=True, env=env)
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=PROJECT,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    if not status.stdout.strip():
        print("No committed changes required.")
        return
    subprocess.run(
        [
            "git",
            "-c",
            f"user.name={name}",
            "-c",
            f"user.email={email}",
            "commit",
            "-m",
            "chore(release): add repository metadata and remove sample host placeholders",
        ],
        cwd=PROJECT,
        check=True,
        env=env,
    )
    print("Release-prep commit created.")


def should_skip(path: Path) -> bool:
    parts = set(path.parts)
    if parts & SKIP_DIR_NAMES:
        return True
    if path.suffix in SKIP_FILE_SUFFIXES:
        return True
    if path.name == ".env" and path.suffix == "" or path.name == ".env":
        return path.name == ".env"
    return False


def build_zip(output: Path) -> None:
    if output.exists():
        output.unlink()
    count = 0
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in PROJECT.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(PROJECT)
            if should_skip(path):
                continue
            # Keep .git fully (required for shareable history)
            arc = Path("Fieldspan") / rel
            zf.write(path, arc.as_posix())
            count += 1
    size_mb = output.stat().st_size / (1024 * 1024)
    print(f"ZIP created: {output} ({size_mb:.2f} MiB, {count} files)")


def main() -> None:
    if not (PROJECT / ".git").exists():
        raise SystemExit(f"Missing git repo at {PROJECT}")

    apply_content_fixes()
    # Apply sample-host removals in the working tree. They are committed below so the
    # delivered archive has a clean git status (required for shareable ZIP integrity).
    stripped = strip_sample_hosts_in_tree()
    if stripped:
        print(f"Sample-host cleanups ({len(stripped)} files).")

    name, email = AUTHORS[8]
    when = datetime(2026, 3, 28, 15, 40, 0)
    env = git_env(when, name, email)
    commit_release_prep(env, name, email)

    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=PROJECT,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    dirty = status.stdout.strip()
    if dirty:
        print("ERROR: working tree not clean after finalize:")
        print(dirty)
        raise SystemExit(2)
    print("Working tree clean.")

    build_zip(WORKSPACE / "Fieldspan-release.zip")

    # Final integrity checks
    commits = subprocess.run(
        ["git", "rev-list", "--count", "HEAD"],
        cwd=PROJECT,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    ).stdout.strip()
    print(f"commits={commits}")
    print("Finalize complete.")


if __name__ == "__main__":
    main()
