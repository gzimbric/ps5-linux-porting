#!/usr/bin/env python3
"""Report the last recognized checkpoint in a private 11.60 capture."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


CHECKPOINTS = [
    ("official-stage0-start", "11.60 stage 0: regular-console diagnostic starting"),
    ("official-stage0-read-pass", "11.60 stage 0: read-only boundary complete"),
    ("official-stage0-pass", "11.60 STAGE 0 PASS"),
    ("official-stage1-start", "11.60 stage 1: regular-console diagnostic starting"),
    ("official-stage1-source-preflight", "11.60 stage 1: source preflight passed"),
    ("official-stage1-target-preflight", "11.60 stage 1: target range preflight passed"),
    ("official-stage1-aliases-verified", "11.60 stage 1: all alias PTEs verified"),
    ("official-stage1-rollback", "11.60 stage 1: rollback verified"),
    ("official-stage1-pass", "11.60 STAGE 1 PASS"),
    ("loader-start", "Welcome to pLinux5-NG"),
    ("initrd-read", "initrd read complete"),
    ("files-loaded", "fetch complete"),
    ("bypass-status", "strike chain="),
    ("bypass-verified", "existing bypass verified"),
    ("handler-validated", "live HV VMMCALL handler validated"),
    ("staging-started", "staging identity map and HV loader"),
    ("bzimage-staged", "bzImage copy complete"),
    ("images-staged", "Linux images staged successfully"),
    ("smp-noop-pass", "SMP self-test: PASS"),
    ("stock-vmmcall-pass", "VMMCALL self-test: PASS"),
    ("handler-passthrough-pass", "HV patch self-test: PASS"),
    ("takeover-armed", "takeover armed"),
    ("unexpected-return", "takeover did not fire"),
]


def classify(text: str) -> dict[str, object]:
    found: list[dict[str, object]] = []
    lines = text.splitlines()
    for number, line in enumerate(lines, 1):
        for name, marker in CHECKPOINTS:
            if marker in line:
                found.append({"checkpoint": name, "line": number})
    bypass_shape = all(
        token in text for token in ("err=0", "self=1", "tgt=16", "wr=16", "ver=16")
    )
    return {
        "recognized": found,
        "last_checkpoint": found[-1]["checkpoint"] if found else None,
        "validated_bypass_shape_present": bypass_shape,
        "linux_boot_observed": "startup_64" in text or "Booting Linux" in text,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("log", type=Path)
    args = parser.parse_args()
    result = classify(args.log.read_text(encoding="utf-8", errors="replace"))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
