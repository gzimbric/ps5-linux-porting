#!/usr/bin/env python3
"""Validate firmware status manifests."""

from __future__ import annotations

import json
import re
from pathlib import Path


SHA256 = re.compile(r"^[0-9a-f]{64}$")
REQUIRED_CHECKPOINTS = {
    "kernel_hook",
    "ktext_redirect",
    "ktext_exec_cave",
    "smp_noop",
    "stock_all_core_vmmcall",
    "live_handler_identity",
    "usb_files_loaded",
    "linux_images_staged",
    "modified_handler_passthrough",
    "identity_cr3",
    "hv_shellcode_entry",
    "all_cpu_linux_barrier",
    "startup_64",
}


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{path}: {exc}"]

    for key in ("schema_version", "firmware", "console_model", "status",
                "linux_booted", "upstream_base", "bypass", "checkpoints",
                "artifacts", "last_observed_marker", "current_boundary"):
        if key not in data:
            errors.append(f"{path}: missing {key}")

    checkpoints = data.get("checkpoints", {})
    missing = REQUIRED_CHECKPOINTS - set(checkpoints)
    if missing:
        errors.append(f"{path}: missing checkpoints {sorted(missing)}")
    for name, value in checkpoints.items():
        if not isinstance(value, bool):
            errors.append(f"{path}: checkpoint {name} is not boolean")

    if data.get("linux_booted") is True and checkpoints.get("startup_64") is not True:
        errors.append(f"{path}: linux_booted requires startup_64")

    bypass = data.get("bypass", {})
    if bypass.get("validated") is True:
        expected = {
            "self_count": 1,
            "target_count": 16,
            "written_count": 16,
            "verified_count": 16,
            "error": 0,
        }
        for key, value in expected.items():
            if bypass.get(key) != value:
                errors.append(f"{path}: validated bypass requires {key}={value}")

    for name, artifact in data.get("artifacts", {}).items():
        digest = artifact.get("sha256", "")
        if not SHA256.fullmatch(digest):
            errors.append(f"{path}: invalid SHA-256 for {name}")
        if artifact.get("included") is not False:
            errors.append(f"{path}: research image {name} must not be included")

    candidate = data.get("candidate_build")
    if candidate is not None:
        if not isinstance(candidate, dict):
            errors.append(f"{path}: candidate_build is not an object")
        else:
            for name, digest in candidate.get("sha256", {}).items():
                if not isinstance(digest, str) or not SHA256.fullmatch(digest):
                    errors.append(
                        f"{path}: invalid candidate SHA-256 for {name}")

    comparison = data.get("architectural_comparison")
    if comparison is not None:
        if not isinstance(comparison, dict):
            errors.append(f"{path}: architectural_comparison is not an object")
        else:
            digest = comparison.get("sha256", "")
            if not isinstance(digest, str) or not SHA256.fullmatch(digest):
                errors.append(f"{path}: invalid architectural comparison SHA-256")
            if comparison.get("included") is not False:
                errors.append(
                    f"{path}: architectural comparison binary must not be included")
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    manifests = sorted((root / "firmwares").glob("*.json"))
    errors = [error for path in manifests for error in validate(path)]
    if errors:
        print("\n".join(f"FAIL {error}" for error in errors))
        return 1
    print(f"PASS {len(manifests)} firmware manifest(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
