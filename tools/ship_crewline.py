#!/usr/bin/env python3
"""Build Crewspan into ./crewspan with a multi-year git history.

Builds in a temporary directory (avoids Windows workspace file locks), then
moves the finished repository (including .git) into ./crewspan.
"""

from __future__ import annotations

import os
import random
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

from tools.authors import AUTHORS
from tools.build_history import (
    FOLLOWUP_COUNT,
    HISTORY_SEED,
    build_all_contents,
    generate_commit_datetimes,
    plan_commits,
    synthesize_followup_commits,
    chunked,
)
import tools.build_history as bh


def _git_env() -> dict[str, str]:
    env = os.environ.copy()
    for key in (
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_COMMON_DIR",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_PREFIX",
    ):
        env.pop(key, None)
    return env


def run(cmd: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged = _git_env()
    if env:
        merged.update(env)
    return subprocess.run(cmd, cwd=cwd, check=True, env=merged, capture_output=True, text=True)


def force_rm(path: Path) -> None:
    if not path.exists():
        return
    for i in range(10):
        shutil.rmtree(path, ignore_errors=True)
        if not path.exists():
            return
        time.sleep(0.5 * (i + 1))
    subprocess.run(["cmd", "/c", "rmdir", "/s", "/q", str(path)], check=False)
    time.sleep(1)
    if path.exists():
        raise SystemExit(f"Unable to remove {path}")


def materialize(root: Path, paths: list[str], contents: dict[str, str]) -> list[str]:
    written: list[str] = []
    for rel in paths:
        if rel not in contents:
            continue
        dest = root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(contents[rel].replace("\r\n", "\n"), encoding="utf-8", newline="\n")
        written.append(rel)
    return written


def git_commit(root: Path, message: str, when: datetime, author_name: str, author_email: str, paths: list[str]) -> bool:
    stamp = when.strftime("%Y-%m-%dT%H:%M:%S")
    env = _git_env()
    env.update(
        {
            "GIT_AUTHOR_DATE": stamp,
            "GIT_COMMITTER_DATE": stamp,
            "GIT_AUTHOR_NAME": author_name,
            "GIT_AUTHOR_EMAIL": author_email,
            "GIT_COMMITTER_NAME": author_name,
            "GIT_COMMITTER_EMAIL": author_email,
        }
    )
    existing = [p for p in paths if (root / p).is_file()]
    if not existing:
        return False
    for batch in chunked(existing, 30):
        try:
            run(["git", "add", "-f", "--", *batch], cwd=root, env=env)
        except subprocess.CalledProcessError:
            for path in batch:
                if (root / path).is_file():
                    run(["git", "add", "-f", "--", path], cwd=root, env=env)
    cached = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=root, env=env)
    if cached.returncode == 0:
        return False
    run(
        [
            "git",
            "-c",
            f"user.name={author_name}",
            "-c",
            f"user.email={author_email}",
            "commit",
            "-m",
            message,
        ],
        cwd=root,
        env=env,
    )
    return True


def patch_tools_into_contents(contents: dict[str, str]) -> None:
    """Ensure codegen tooling paths are sourced from the workspace tools/ tree."""
    skip = {
        "tools/build_history.py",
        "tools/run_bootstrap.py",
        "tools/zip_release.py",
        "tools/ship_crewspan.py",
        "tools/build_cascaderelay.py",
    }
    tools_root = WORKSPACE / "tools"
    for path in tools_root.rglob("*"):
        if not path.is_file() or "__pycache__" in path.parts or "cascaderelay" in path.parts:
            continue
        if path.suffix in {".pyc", ".pyo"}:
            continue
        rel = path.relative_to(WORKSPACE).as_posix()
        if rel in skip:
            continue
        try:
            contents[rel] = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue


def main() -> None:
    project = WORKSPACE / "crewspan"
    print("Generating source tree…")
    # Codegen staging + tooling paths resolve against the workspace.
    bh.ROOT = WORKSPACE
    contents = build_all_contents()
    patch_tools_into_contents(contents)
    print(f"  {len(contents)} files staged")

    rng = random.Random(HISTORY_SEED)
    planned = plan_commits(sorted(contents.keys()), contents, rng)
    follow = synthesize_followup_commits(contents, FOLLOWUP_COUNT, rng)

    build_dir = Path(tempfile.mkdtemp(prefix="crewspan_hist_"))
    print(f"Replaying history in {build_dir}…")
    bh.ROOT = build_dir

    run(["git", "init", "-b", "main"], cwd=build_dir)
    follow_start = len(planned)
    planned.extend(edit.spec for edit in follow)
    follow_by_index = {follow_start + i: edit for i, edit in enumerate(follow)}
    dates = generate_commit_datetimes(len(planned))
    print(f"  {len(planned)} commits from {dates[0].date()} to {dates[-1].date()}")

    committed = 0
    for i, (spec, when) in enumerate(zip(planned, dates)):
        if not (build_dir / ".git" / "HEAD").exists():
            raise SystemExit(f".git missing at commit {i + 1}")
        edit = follow_by_index.get(i)
        if edit is not None:
            contents[edit.spec.paths[0]] = edit.updated_text
        materialize(build_dir, spec.paths, contents)
        name, email = AUTHORS[spec.author_index % len(AUTHORS)]
        if git_commit(build_dir, spec.message, when, name, email, spec.paths):
            committed += 1
        if (i + 1) % 40 == 0 or i + 1 == len(planned):
            print(f"  … {i + 1}/{len(planned)} {spec.message[:70]}")

    authors_out = run(["git", "log", "--format=%an <%ae>"], cwd=build_dir)
    approved = {f"{n} <{e}>" for n, e in AUTHORS}
    bad = sorted({a for a in authors_out.stdout.splitlines() if a and a not in approved})
    if bad:
        raise SystemExit(f"Unexpected authors: {bad}")

    print(f"Publishing to {project}…")
    # Publish via a sibling folder first so a locked previous tree cannot block the move.
    staged = project.parent / "crewspan_publish"
    force_rm(staged)
    shutil.move(str(build_dir), str(staged))
    force_rm(project)
    if project.exists():
        # Fall back: keep published tree under crewspan_publish if swap is locked.
        print(f"WARNING: could not replace {project}; leaving build at {staged}")
        project = staged
    else:
        staged.rename(project)

    # Stats
    log = run(["git", "log", "--format=%ad%x09%an", "--date=short"], cwd=project)
    lines = [ln for ln in log.stdout.splitlines() if ln.strip()]
    dates_s = [ln.split("\t")[0] for ln in lines]
    file_count = sum(1 for p in project.rglob("*") if p.is_file() and ".git" not in p.parts)
    loc = 0
    for path in project.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.suffix in {".py", ".ts", ".tsx", ".js", ".jsx", ".md", ".yml", ".yaml", ".toml", ".json", ".css", ".html", ".sh"}:
            try:
                loc += sum(1 for _ in path.open(encoding="utf-8", errors="ignore"))
            except OSError:
                pass

    print("\n=== Crewspan history stats ===")
    print(f"Commits:     {committed}")
    print(f"Date range:  {min(dates_s)} .. {max(dates_s)}")
    print(f"Files:       {file_count}")
    print(f"Approx LOC:  {loc:,}")
    print(f"Location:    {project}")


if __name__ == "__main__":
    main()
# history-note: evolutionary edit 2
