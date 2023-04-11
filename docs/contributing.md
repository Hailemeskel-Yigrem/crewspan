# Contributing

## Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- PostgreSQL 15+ and Redis 7+ (or use Docker)

## Setup

```bash
git clone <repo-url> RelayOps && cd RelayOps
cp .env.example .env
make install
make up
make migrate
make seed
```

## Code Generation

Regenerate domain modules from specifications:

```bash
python -m tools.codegen.generate_api
python -m tools.codegen.generate_web
python -m tools.codegen.generate_tests
python -m tools.codegen.generate_docs
python -m tools.codegen.generate_infra
```

Or bootstrap everything:

```python
from pathlib import Path
from tools.codegen import generate_api_tree, generate_web_tree, generate_tests_tree, generate_docs_tree, generate_infra_tree

root = Path(".")
generate_api_tree(root)
generate_web_tree(root)
generate_tests_tree(root)
generate_docs_tree(root)
generate_infra_tree(root)
```

## Code Standards

- **Python:** Ruff formatter/linter, type hints required, async SQLAlchemy
- **TypeScript:** Strict mode, functional React components, CSS variables for theming
- **Commits:** Conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`)
- **Tests:** Required for new domain methods and UI components

## Pre-commit

```bash
pre-commit install
pre-commit run --all-files
```
