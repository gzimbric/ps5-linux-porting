#!/usr/bin/env python3
"""Reject likely private or binary research artifacts before publication."""

from __future__ import annotations

import ipaddress
import re
from pathlib import Path


DENIED_SUFFIXES = {
    ".bin", ".elf", ".o", ".a", ".so", ".sprx", ".img", ".xz",
    ".dump", ".dmp", ".core", ".zip", ".tar", ".tgz", ".gz", ".7z",
    ".log",
}
DENIED_NAMES = re.compile(
    r"(private[_-]?key|console[_-]?key|root[_-]?key|secret)", re.I
)
PRIVATE_TEXT = (
    "-----BEGIN PRIVATE KEY-----",
    "-----BEGIN OPENSSH PRIVATE KEY-----",
    "/Users/",
    "C:\\Users\\",
)
IPV4 = re.compile(r"(?<![0-9.])(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?![0-9.])")
MAX_FILE = 1_000_000


def is_private_ipv4(value: str) -> bool:
    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        return False
    return ip.is_private and not ip.is_loopback


def check(root: Path) -> list[str]:
    errors: list[str] = []
    for path in root.rglob("*"):
        if (
            not path.is_file()
            or ".git" in path.parts
            or "__pycache__" in path.parts
            or path.resolve() == Path(__file__).resolve()
        ):
            continue
        rel = path.relative_to(root)
        if path.suffix.lower() in DENIED_SUFFIXES:
            errors.append(f"denied binary/archive suffix: {rel}")
        if DENIED_NAMES.search(path.name):
            errors.append(f"sensitive-looking filename: {rel}")
        if path.stat().st_size > MAX_FILE:
            errors.append(f"file exceeds {MAX_FILE} bytes: {rel}")
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"non-text file: {rel}")
            continue
        for marker in PRIVATE_TEXT:
            if marker in content:
                errors.append(f"private path or key marker {marker!r}: {rel}")
        for candidate in IPV4.findall(content):
            if is_private_ipv4(candidate):
                errors.append(f"private IPv4 address {candidate}: {rel}")
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = check(root)
    if errors:
        for error in errors:
            print(f"FAIL {error}")
        return 1
    print("PASS public-tree check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
