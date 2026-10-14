#!/usr/bin/env python3
"""Check local Markdown links without making network requests."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote


LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def check(root: Path) -> list[str]:
    errors: list[str] = []
    for path in root.rglob("*.md"):
        if ".git" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for raw in LINK.findall(text):
            target = raw.split("#", 1)[0]
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            candidate = (path.parent / unquote(target)).resolve()
            if not candidate.exists():
                errors.append(f"{path.relative_to(root)}: missing {raw}")
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = check(root)
    if errors:
        print("\n".join(f"FAIL {error}" for error in errors))
        return 1
    print("PASS local Markdown links")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
