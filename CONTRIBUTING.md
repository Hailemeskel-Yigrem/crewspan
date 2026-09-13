# Contributing

## Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose (for Postgres 15 and Redis 7)

## Setup

```bash
git clone https://github.com/Hailemeskel-Yigrem/crewspan.git && cd crewspan
cp .env.example .env
make install
make up
make migrate
make seed
```

`make install` installs from the committed lockfiles
(`apps/api/requirements.lock.txt`, `apps/worker/requirements.lock.txt`,
`apps/web/package-lock.json`), so every machine resolves the same versions.

## Branching

Branch off `main` using `<type>/<short-description>`, matching the commit
types below — for example `fix/schedule-overlap-guard` or
`docs/deployment-runbook`.

## Running checks locally

Run these before opening a pull request; CI runs the same commands and fails
the build on any of them.

```bash
make test        # pytest (api, worker, packages) + vitest
make lint        # ruff + eslint
make typecheck   # mypy + tsc --noEmit
make coverage    # test suites with their coverage floors enforced
```

To run one suite directly:

```bash
pytest apps/api/tests -v
cd apps/web && npm test
```

## Dependencies

Manifests are the source of truth; lockfiles are generated. After editing a
manifest, regenerate and commit the lockfile in the same change:

```bash
pip-compile --strip-extras --output-file apps/api/requirements.lock.txt apps/api/requirements.txt
cd apps/web && npm install
```

## Code standards

- **Python:** ruff (config in `ruff.toml`), type hints required, async SQLAlchemy.
- **TypeScript:** strict mode, functional components, CSS variables for theming.
- **Commits:** conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`,
  `test:`, `build:`, `ci:`, `chore:`).
- **Tests:** a behaviour change lands with its test in the same commit. Name the
  test file in the commit body, e.g.
  `fix: reject overlapping schedule intervals (apps/api/tests/unit/test_schedule_service.py)`.

## Coverage

Both suites enforce a floor rather than a target. The thresholds in
`apps/api/pyproject.toml` and `apps/web/vite.config.ts` sit just under the
current measured coverage, so a regression fails CI. Raise them when you add
tests — never lower them to make a build pass.

## Pull requests

- Keep a PR to one logical change; a red CI run blocks merge.
- Describe the behaviour change and how you verified it.
- Update `CHANGELOG.md` under `## [Unreleased]`.

## Pre-commit

```bash
pre-commit install
pre-commit run --all-files
```
