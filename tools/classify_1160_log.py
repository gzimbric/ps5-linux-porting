#!/usr/bin/env python3
"""Report the last recognized checkpoint in a private 11.60 capture."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


CHECKPOINTS = [
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
