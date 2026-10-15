#!/usr/bin/env python3
"""Validate firmware status manifests."""

from __future__ import annotations

import json
import re
from pathlib import Path


SHA256 = re.compile(r"^[0-9a-f]{64}$")
GIT_COMMIT = re.compile(r"^[0-9a-f]{40}$")
REQUIRED_CHECKPOINTS = {
    "kernel_hook",
    "ktext_redirect",
    "ktext_exec_cave",
    "smp_noop",
    "stock_all_core_vmmcall",
    "live_handler_identity",
    "usb_files_loaded",
    "linux_images_staged",
    "bounded_stage0_read_only",
    "bounded_stage1_alias_transaction",
    "bounded_stage1_alias_install",
    "bounded_stage1_alias_verify",
    "bounded_stage1_rollback_verify",
    "bounded_stage1b_alias_read_through",
    "syscore_alias_read_through",
    "prepare_resume_staging",
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
                "bounded_loader_diagnostics", "artifacts",
                "last_observed_marker", "current_boundary"):
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

    bounded = data.get("bounded_loader_diagnostics")
    if not isinstance(bounded, dict):
        errors.append(f"{path}: bounded_loader_diagnostics is not an object")
    else:
        source_commit = bounded.get("source_commit", "")
        if not isinstance(source_commit, str) or not GIT_COMMIT.fullmatch(source_commit):
            errors.append(f"{path}: invalid bounded diagnostic source commit")

        stage0 = bounded.get("stage0")
        stage1 = bounded.get("stage1")
        stage1b = bounded.get("stage1b")
        stage2a = bounded.get("stage2a")
        if not isinstance(stage0, dict):
            errors.append(f"{path}: bounded stage0 is not an object")
        else:
            digest = stage0.get("sha256", "")
            if not isinstance(digest, str) or not SHA256.fullmatch(digest):
                errors.append(f"{path}: invalid bounded stage0 SHA-256")
            if stage0.get("result") != "pass-responsive":
                errors.append(f"{path}: bounded stage0 result is not pass-responsive")
            if stage0.get("page_table_writes") != 0:
                errors.append(f"{path}: bounded stage0 must have zero page-table writes")

        if not isinstance(stage1, dict):
            errors.append(f"{path}: bounded stage1 is not an object")
        else:
            digest = stage1.get("sha256", "")
            if not isinstance(digest, str) or not SHA256.fullmatch(digest):
                errors.append(f"{path}: invalid bounded stage1 SHA-256")
            if stage1.get("result") != "pass-responsive":
                errors.append(f"{path}: bounded stage1 result is not pass-responsive")
            logical_pages = stage1.get("logical_16k_pages")
            leaf_ptes = stage1.get("leaf_ptes")
            journaled_writes = stage1.get("journaled_writes")
            temporary_pages = stage1.get("temporary_table_pages")
            counts = (logical_pages, leaf_ptes, journaled_writes, temporary_pages)
            if any(not isinstance(value, int) or isinstance(value, bool) or value <= 0
                   for value in counts):
                errors.append(f"{path}: invalid bounded stage1 counts")
            elif leaf_ptes != logical_pages * 4 or journaled_writes < leaf_ptes:
                errors.append(f"{path}: inconsistent bounded stage1 counts")
            if stage1.get("rollback_verified") is not True:
                errors.append(f"{path}: bounded stage1 rollback is not verified")
            aliases_dereferenced = stage1.get("aliases_dereferenced")
            if aliases_dereferenced is not False:
                errors.append(f"{path}: bounded stage1 must not dereference aliases")

        if not isinstance(stage1b, dict):
            errors.append(f"{path}: bounded stage1b is not an object")
        else:
            digest = stage1b.get("sha256", "")
            if not isinstance(digest, str) or not SHA256.fullmatch(digest):
                errors.append(f"{path}: invalid bounded stage1b SHA-256")
            source_commit = stage1b.get("source_commit", "")
            if (not isinstance(source_commit, str) or
                    not GIT_COMMIT.fullmatch(source_commit)):
                errors.append(f"{path}: invalid bounded stage1b source commit")
            if stage1b.get("result") != "pass-responsive-cold-reboot-required":
                errors.append(
                    f"{path}: bounded stage1b result must require cold reboot")
            expected_counts = {
                "data_bytes": 16384,
                "leaf_ptes": 4,
                "accessed_bits_observed": 4,
                "locked_backing_bytes": 65536,
            }
            for name, expected in expected_counts.items():
                if stage1b.get(name) != expected:
                    errors.append(
                        f"{path}: bounded stage1b requires {name}={expected}")
            required_true = (
                "rollback_verified",
                "aliases_dereferenced",
                "cold_reboot_required",
            )
            for name in required_true:
                if stage1b.get(name) is not True:
                    errors.append(f"{path}: bounded stage1b requires {name}=true")
            required_false = ("pid1_context", "tlb_shootdown", "executable_leaves")
            for name in required_false:
                if stage1b.get(name) is not False:
                    errors.append(f"{path}: bounded stage1b requires {name}=false")
            if (checkpoints.get("syscore_alias_read_through") !=
                    stage1b.get("aliases_dereferenced")):
                errors.append(
                    f"{path}: syscore read-through disagrees with aliases_dereferenced")

        if not isinstance(stage2a, dict):
            errors.append(f"{path}: bounded stage2a is not an object")
        else:
            for name in ("sha256", "wake_blob_sha256"):
                digest = stage2a.get(name, "")
                if not isinstance(digest, str) or not SHA256.fullmatch(digest):
                    errors.append(f"{path}: invalid bounded stage2a {name}")
            source_commit = stage2a.get("source_commit", "")
            if (not isinstance(source_commit, str) or
                    not GIT_COMMIT.fullmatch(source_commit)):
                errors.append(f"{path}: invalid bounded stage2a source commit")
            if stage2a.get("result") != "pass-responsive-cold-reboot-required":
                errors.append(
                    f"{path}: bounded stage2a result must be responsive and require cold reboot")
            expected_counts = {
                "wake_blob_bytes": 240,
                "mapped_bytes": 16384,
                "leaf_ptes": 4,
            }
            for name, expected in expected_counts.items():
                if stage2a.get(name) != expected:
                    errors.append(
                        f"{path}: bounded stage2a requires {name}={expected}")
            required_true = (
                "pid1_mapping",
                "ui_responsive",
                "cold_reboot_required",
            )
            for name in required_true:
                if stage2a.get(name) is not True:
                    errors.append(f"{path}: bounded stage2a requires {name}=true")
            required_false = (
                "executed",
                "resume_hook_armed",
                "hypervisor_modified",
                "rest_mode_entered",
            )
            for name in required_false:
                if stage2a.get(name) is not False:
                    errors.append(f"{path}: bounded stage2a requires {name}=false")
            if checkpoints.get("prepare_resume_staging") is not True:
                errors.append(
                    f"{path}: stage2a pass requires prepare_resume_staging=true")

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
    if candidate is None:
        candidate = data.get("superseded_candidate_build")
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
