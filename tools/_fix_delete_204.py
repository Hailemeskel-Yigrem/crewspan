"""Fix FastAPI 204 delete handlers that assert on empty-body responses."""

from __future__ import annotations

from pathlib import Path

ROOT = Path("apps/api/app/domains")


def main() -> None:
    for path in ROOT.glob("*/router.py"):
        text = path.read_text(encoding="utf-8")
        if "HTTP_204_NO_CONTENT" not in text:
            continue
        if "response_class=Response" in text:
            print("ok", path)
            continue

        updated = text.replace(
            '@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)',
            '@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)',
            1,
        )
        updated = updated.replace(
            ") -> None:\n    await service.delete(entity_id, tenant_id=tenant_id)",
            ") -> Response:\n    await service.delete(entity_id, tenant_id=tenant_id)\n    return Response(status_code=status.HTTP_204_NO_CONTENT)",
            1,
        )

        if "from fastapi import Response" not in updated and "Response," not in updated.split("\n", 20)[0:20].__repr__():
            if "from fastapi import " in updated:
                updated = updated.replace("from fastapi import ", "from fastapi import Response, ", 1)
            else:
                updated = "from fastapi import Response\n" + updated

        # Ensure Response import once
        lines = updated.splitlines()
        fastapi_imports = [i for i, line in enumerate(lines) if line.startswith("from fastapi import ")]
        if fastapi_imports:
            idx = fastapi_imports[0]
            if "Response" not in lines[idx]:
                lines[idx] = lines[idx].replace("from fastapi import ", "from fastapi import Response, ", 1)
            updated = "\n".join(lines) + "\n"

        path.write_text(updated, encoding="utf-8", newline="\n")
        print("patched", path)


if __name__ == "__main__":
    main()
