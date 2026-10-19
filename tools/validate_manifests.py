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
    "mp3_commands_21_22_present_in_successful_path",
    "display_operation_table_present_in_successful_path",
    "individual_mp3_and_table_returns_observed",
}


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{path}: {exc}"]

    for key in ("schema_version", "firmware", "console_model", "status",
                "linux_booted", "upstream_base", "bypass", "checkpoints",
                "bounded_loader_diagnostics", "sonic_display_diagnostics",
                "ubuntu_control", "ubuntu_wifi",
                "boot_media", "artifacts",
                "latest_authenticated_working_run", "latest_tested_run",
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

    if checkpoints.get("mp3_commands_21_22_present_in_successful_path") is not True:
        errors.append(f"{path}: Run 15 must record MP3 commands in the containing path")
    if checkpoints.get("display_operation_table_present_in_successful_path") is not True:
        errors.append(f"{path}: Run 15 must record the display table in the containing path")
    if checkpoints.get("individual_mp3_and_table_returns_observed") is not False:
        errors.append(f"{path}: individual MP3/table return scope is overstated")

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

    display = data.get("sonic_display_diagnostics")
    if not isinstance(display, dict):
        errors.append(f"{path}: sonic_display_diagnostics is not an object")
    else:
        source_commit = display.get("last_tested_source_commit", "")
        if not isinstance(source_commit, str) or not GIT_COMMIT.fullmatch(source_commit):
            errors.append(f"{path}: invalid display diagnostic source commit")
        expected_sizes = {
            "run10": (169840, 11992),
            "run11": (169840, 11992),
            "run12": (169840, 11992),
            "run13": (169840, 11992),
            "run14": (169872, 12024),
            "run15": (169872, 12024),
        }
        for run_name, (elf_size, wake_size) in expected_sizes.items():
            run = display.get(run_name)
            if not isinstance(run, dict):
                errors.append(f"{path}: display diagnostic {run_name} is not an object")
                continue
            run_commit = run.get("source_commit", "")
            if not isinstance(run_commit, str) or not GIT_COMMIT.fullmatch(run_commit):
                errors.append(f"{path}: invalid {run_name} source commit")
            for name in ("elf_sha256", "wake_sha256"):
                digest = run.get(name, "")
                if not isinstance(digest, str) or not SHA256.fullmatch(digest):
                    errors.append(f"{path}: invalid {run_name} {name}")
            if (run.get("elf_size") != elf_size or
                    run.get("wake_size") != wake_size):
                errors.append(f"{path}: unexpected {run_name} artifact size")
        run12 = display.get("run12", {})
        if run12.get("authenticated_working_baseline") is not True:
            errors.append(f"{path}: run12 authenticated baseline is missing")
        run13 = display.get("run13", {})
        if run13.get("attempts") != 2:
            errors.append(f"{path}: run13 must record two failed attempts")
        run14 = display.get("run14", {})
        if run14.get("initializer_only_control") is not True:
            errors.append(f"{path}: run14 must be recorded as the initializer-only control")
        if run14.get("mp3_initialize_validated") is not True:
            errors.append(f"{path}: run14 must validate MP3 initialization")
        if run14.get("runtime_clear_executed") is not False:
            errors.append(f"{path}: run14 must keep the runtime clear disabled")
        for name in ("wake_elf_sha256", "clear_enabled_control_wake_sha256"):
            digest = run14.get(name, "")
            if not isinstance(digest, str) or not SHA256.fullmatch(digest):
                errors.append(f"{path}: invalid run14 {name}")
        if run14.get("wake_elf_size") != 18384:
            errors.append(f"{path}: unexpected run14 wake ELF size")
        run15 = display.get("run15", {})
        if run15.get("release_loader_baseline") is not True:
            errors.append(f"{path}: run15 must be the release loader baseline")
        if run15.get("visible_display_observed") is not True:
            errors.append(f"{path}: run15 must record the observed physical display")
        if run15.get("runtime_clear_executed") is not False:
            errors.append(f"{path}: run15 must keep the runtime clear disabled")
        if run15.get("display_table_operations") != 29:
            errors.append(f"{path}: run15 must enable all 29 display operations")
        if run15.get("mp3_commands") != [21, 22]:
            errors.append(f"{path}: run15 must issue MP3 commands 21 and 22")
        if run15.get("per_operation_return_values_observed") is not False:
            errors.append(f"{path}: run15 per-operation telemetry scope is overstated")
        digest = run15.get("wake_elf_sha256", "")
        if not isinstance(digest, str) or not SHA256.fullmatch(digest):
            errors.append(f"{path}: invalid run15 wake_elf_sha256")
        if run15.get("wake_elf_size") != 18448:
            errors.append(f"{path}: unexpected run15 wake ELF size")
        baselines = [name for name, run in display.items()
                     if isinstance(run, dict) and
                     run.get("release_loader_baseline") is True]
        if baselines != ["run15"]:
            errors.append(f"{path}: exactly one release loader baseline (run15) expected, got {baselines}")
        if checkpoints.get("visible_hdmi") is not run15.get("visible_display_observed"):
            errors.append(f"{path}: visible_hdmi checkpoint disagrees with run15")
        release = display.get("release")
        if not isinstance(release, dict):
            errors.append(f"{path}: display release is not an object")
        else:
            for name in ("elf_sha256", "source_zip_sha256"):
                digest = release.get(name, "")
                if not isinstance(digest, str) or not SHA256.fullmatch(digest):
                    errors.append(f"{path}: invalid release {name}")
            if release.get("elf_sha256") != run15.get("elf_sha256"):
                errors.append(f"{path}: release ELF must be byte-identical to run15")
            if release.get("source_commit") != run15.get("source_commit"):
                errors.append(f"{path}: release source commit must match run15")
            if release.get("included") is not False:
                errors.append(f"{path}: release binary must not be included")
            published = release.get("published_source")
            if not isinstance(published, dict):
                errors.append(f"{path}: release published_source is not an object")
            else:
                for name in ("commit", "tree", "release_check_commit"):
                    value = published.get(name, "")
                    if not isinstance(value, str) or not GIT_COMMIT.fullmatch(value):
                        errors.append(f"{path}: invalid published source {name}")
                if published.get("tree_identical_to_source_commit") is not True:
                    errors.append(f"{path}: published source must match the tested tree")
                if published.get("release_check_reproduces_run15_artifacts") is not True:
                    errors.append(f"{path}: release check must reproduce Run 15 artifacts")
                if published.get("binaries_included") is not False:
                    errors.append(f"{path}: published source must not include binaries")
        if display.get("production_runtime_clear_required") is not False:
            errors.append(f"{path}: 11.60 production must omit the runtime clear")
        if display.get("next_boundary_validated") is not False:
            errors.append(f"{path}: next display boundary must remain unvalidated")

    ubuntu = data.get("ubuntu_control")
    if not isinstance(ubuntu, dict):
        errors.append(f"{path}: ubuntu_control is not an object")
    else:
        if ubuntu.get("run") != 16:
            errors.append(f"{path}: Ubuntu control must be Run 16")
        if ubuntu.get("result") != "pass-physical-display-authenticated-wired-ssh":
            errors.append(f"{path}: unexpected Ubuntu control result")
        if ubuntu.get("same_console_as_run15") is not True:
            errors.append(f"{path}: Ubuntu control must record same-console scope")
        if ubuntu.get("independent_hardware_reproduction") is not False:
            errors.append(f"{path}: Ubuntu control must not claim independent reproduction")
        image_builder = ubuntu.get("image_builder")
        if not isinstance(image_builder, dict):
            errors.append(f"{path}: Ubuntu image_builder is not an object")
        else:
            expected_builder = {
                "upstream_repository": "https://github.com/ps5-linux/ps5-linux-image",
                "upstream_base_commit": "52db0a42302e4a6b5420a11fa00a84841ea5db56",
                "published_repository": "https://github.com/gzimbric/ps5-linux-image",
                "published_branch": "ubuntu2404-1160-tested",
            }
            for name, expected in expected_builder.items():
                if image_builder.get(name) != expected:
                    errors.append(
                        f"{path}: unexpected Ubuntu image builder {name}")
            if image_builder.get("customized_from_upstream") is not True:
                errors.append(f"{path}: Ubuntu image must be marked as customized")
            if image_builder.get("kernel_input_source") != (
                "separate-deterministic-run15-baseline-build"
            ):
                errors.append(f"{path}: unexpected Ubuntu kernel input source")
            if image_builder.get("fixed_kbuild_user_and_host") is not True:
                errors.append(f"{path}: Ubuntu kernel KBUILD boundary is missing")
            if image_builder.get("date_shim_used") is not True:
                errors.append(f"{path}: Ubuntu kernel date-shim boundary is missing")
            if image_builder.get("deterministic_kernel_recipe_integrated") is not True:
                errors.append(
                    f"{path}: Ubuntu deterministic kernel recipe is not integrated")
            if image_builder.get("kernel_package_reused") is not True:
                errors.append(
                    f"{path}: Ubuntu image assembly must record kernel package reuse")
            for field in (
                "clean_kernel_build_validated",
                "full_clean_image_build_validated",
                "one_command_reproduction_validated",
            ):
                if not isinstance(image_builder.get(field), bool):
                    errors.append(
                        f"{path}: Ubuntu image builder {field} is not boolean")
            if (image_builder.get("full_clean_image_build_validated") is True and
                    image_builder.get("clean_kernel_build_validated") is not True):
                errors.append(
                    f"{path}: Ubuntu clean full-image validation requires clean kernel validation")
            if (image_builder.get("one_command_reproduction_validated") is True and
                    (image_builder.get("clean_kernel_build_validated") is not True or
                     image_builder.get("full_clean_image_build_validated") is not True)):
                errors.append(
                    f"{path}: Ubuntu one-command validation requires both clean build gates")
            if image_builder.get("binaries_included") is not False:
                errors.append(f"{path}: Ubuntu image source must not include binaries")
            pin_complete = image_builder.get("pin_complete")
            published_commit = image_builder.get("published_commit", "")
            published_tree = image_builder.get("published_tree", "")
            if pin_complete is not True:
                errors.append(f"{path}: Ubuntu tested source pin must be complete")
            if (not isinstance(published_commit, str) or
                    not GIT_COMMIT.fullmatch(published_commit)):
                errors.append(f"{path}: invalid published Ubuntu source commit")
            if (not isinstance(published_tree, str) or
                    not GIT_COMMIT.fullmatch(published_tree)):
                errors.append(f"{path}: invalid published Ubuntu source tree")

        disk_image = ubuntu.get("disk_image")
        if not isinstance(disk_image, dict):
            errors.append(f"{path}: Ubuntu disk_image is not an object")
        else:
            if disk_image.get("size") != 16777216000:
                errors.append(f"{path}: unexpected Ubuntu disk image size")
            if disk_image.get("sha256") != (
                "bf4bca3ab6583c74eb06b17e8c3e4243972690a38fa40bd9a652c6d71a7ee347"
            ):
                errors.append(f"{path}: unexpected Ubuntu disk image SHA-256")
            if disk_image.get("included") is not False:
                errors.append(f"{path}: Ubuntu disk image must not be included")
            if disk_image.get("byte_identity_required_by_loader") is not False:
                errors.append(f"{path}: Ubuntu whole-image identity is not a loader gate")

        expected_partitions = {
            "logical_sector_size": 512,
            "partition_numbers_follow_physical_order": False,
            "root": {
                "number": 1,
                "filesystem": "ext4",
                "label": "ubuntu2404",
                "start_sector": 1024000,
                "end_sector": 32765951,
                "size_sectors": 31741952,
            },
            "efi": {
                "number": 2,
                "filesystem": "fat32",
                "label": "boot",
                "start_sector": 2048,
                "end_sector": 1023999,
                "size_sectors": 1021952,
            },
        }
        if ubuntu.get("partitions") != expected_partitions:
            errors.append(f"{path}: unexpected Ubuntu partition layout")

        expected_artifacts = {
            "loader": (169872, "422b87ec39ca0edfce8dddd609c2eff1cc7adcb2732b7909b76fafbd60dd2336"),
            "kernel": (12702720, "11280a8f5ca197ee5458fd446a4dadf2d0b5d0ef6218583cbe6325ee34e99cde"),
            "initramfs_unpadded": (50803483, "996bc02a64404bc84d06c8df0c4143b66932d8af8549f39c82c71677fdec58c9"),
            "initrd": (54376639, "2eef0352879e091083450b799c75514a450f4110cbc747f640962fdde2dc06c8"),
            "cmdline": (121, "6b3c09112fe049d3cbeada65fb3c82bb0f5fcaddce6c0709051df3d9f5a79f6d"),
            "vram": (11, "bc4642feb06a4cc6d10d5865e321efaad7ab3f3f1d5d025151b79978164310a0"),
            "kexec": (136, "0f26e09911a8a2bc9912d7c77fee6ac09ccd18a820086cb103be92de081b6c52"),
        }
        for name, (size, digest) in expected_artifacts.items():
            artifact = ubuntu.get(name)
            if not isinstance(artifact, dict):
                errors.append(f"{path}: Ubuntu control {name} is not an object")
                continue
            if artifact.get("size") != size:
                errors.append(f"{path}: unexpected Ubuntu control {name} size")
            if artifact.get("sha256") != digest:
                errors.append(f"{path}: unexpected Ubuntu control {name} SHA-256")
        initrd = ubuntu.get("initrd", {})
        if initrd.get("zero_padding_bytes") != 3573156:
            errors.append(f"{path}: unexpected Ubuntu initrd padding")
        unpadded = ubuntu.get("initramfs_unpadded", {})
        unpadded_size = unpadded.get("size") if isinstance(unpadded, dict) else None
        padding_size = initrd.get("zero_padding_bytes") if isinstance(initrd, dict) else None
        efi_size = initrd.get("size") if isinstance(initrd, dict) else None
        sizes = (unpadded_size, padding_size, efi_size)
        if (not all(isinstance(value, int) and not isinstance(value, bool)
                    for value in sizes) or
                unpadded_size + padding_size != efi_size):
            errors.append(f"{path}: inconsistent Ubuntu initrd padding arithmetic")
        if initrd.get("byte_identical_to_run15") is not False:
            errors.append(f"{path}: Ubuntu initrd must differ from Run 15")
        loader = ubuntu.get("loader", {})
        if loader.get("byte_identical_to_run15") is not True:
            errors.append(f"{path}: Ubuntu control must reuse the Run 15 loader")
        wireless = ubuntu.get("wireless", {})
        if wireless.get("mt7921_applicable") is not False:
            errors.append(f"{path}: Ubuntu control must reject MT7921 for this hardware")

    wifi = data.get("ubuntu_wifi")
    if not isinstance(wifi, dict):
        errors.append(f"{path}: ubuntu_wifi is not an object")
    else:
        if wifi.get("run") != 17:
            errors.append(f"{path}: Ubuntu Wi-Fi bring-up must be Run 17")
        if wifi.get("result") != "pass-scan-associate-download":
            errors.append(f"{path}: unexpected Ubuntu Wi-Fi result")
        if wifi.get("independent_hardware_reproduction") is not False:
            errors.append(f"{path}: Ubuntu Wi-Fi must not claim independent reproduction")
        loader = wifi.get("loader", {})
        if (loader.get("sha256") !=
                "422b87ec39ca0edfce8dddd609c2eff1cc7adcb2732b7909b76fafbd60dd2336" or
                loader.get("byte_identical_to_run15") is not True):
            errors.append(f"{path}: Ubuntu Wi-Fi must reuse the Run 15 loader")
        if wifi.get("first_wake_cause_isolated") is not False:
            errors.append(f"{path}: Ubuntu Wi-Fi wake-stall cause is overstated")
        driver = wifi.get("driver", {})
        expected_driver = {
            "repository": "https://github.com/ps5-linux/ps5-linux-mwifiex",
            "commit": "4aff9085530a3cdf7d5fbb124c006cc299ac3605",
            "nxp_repository": "https://github.com/nxp-imx/mwifiex",
            "nxp_branch": "lf-6.18.2_1.0.0",
            "nxp_commit": "a5fe4e194bf99315e349d81d77d6dfacec70757a",
            "patches": [
                "ps5-iw620.patch",
                "ps5-iw620-cmd-timeout-recover.patch",
                "ps5-iw620-kernel71-compat.patch",
                "ps5-iw620-rtnl-bounded-wait.patch",
            ],
        }
        for name, expected in expected_driver.items():
            if driver.get(name) != expected:
                errors.append(f"{path}: unexpected Ubuntu Wi-Fi driver {name}")
        if driver.get("kernel72_compat_applied") is not False:
            errors.append(f"{path}: the 7.2 compatibility patch does not build on 7.1.7")
        if driver.get("objtool_disabled") is not False:
            errors.append(f"{path}: Wi-Fi modules must be built with objtool")
        if driver.get("binaries_included") is not False:
            errors.append(f"{path}: Wi-Fi driver modules must not be included")
        expected_modules = {
            "mlan": (1491280, "e6f8e649974767f26d9bd8c60b3b49e1203d5282700493864b7e6fd7be482b23"),
            "moal": (2112848, "3e00f26af4d71d6f459a56a1b99c435dcacb09d3ead28e0e722898a68a6347ed"),
        }
        modules = wifi.get("modules", {})
        for name, (size, digest) in expected_modules.items():
            module = modules.get(name) if isinstance(modules, dict) else None
            if not isinstance(module, dict):
                errors.append(f"{path}: Ubuntu Wi-Fi module {name} is not an object")
                continue
            if module.get("size") != size:
                errors.append(f"{path}: unexpected Ubuntu Wi-Fi module {name} size")
            if module.get("sha256") != digest:
                errors.append(f"{path}: unexpected Ubuntu Wi-Fi module {name} SHA-256")
        firmware = wifi.get("firmware", {})
        expected_firmware = {
            "name": "nxp/pcieuartiw620_combo_v1.bin",
            "size": 498108,
            "sha256": "eafef24af118f96f84a652e17aeed555ec4ac719b9fac11ff98a2de7e2b4b369",
            "version": "17.130.3.p47",
            "ktext_offset": "0x1585D90",
            "size_hex": "0x799BC",
        }
        for name, expected in expected_firmware.items():
            if firmware.get(name) != expected:
                errors.append(f"{path}: unexpected Ubuntu Wi-Fi firmware {name}")
        try:
            size_matches = int(firmware.get("size_hex", ""), 16) == firmware.get("size")
        except (TypeError, ValueError):
            size_matches = False
        if not size_matches:
            errors.append(f"{path}: inconsistent Ubuntu Wi-Fi firmware size")
        if firmware.get("included") is not False:
            errors.append(f"{path}: Wi-Fi firmware must not be included")
        if firmware.get("loader_dump_hardware_tested") is not False:
            errors.append(f"{path}: the 11.60 loader firmware dump has not run on hardware")
        for field in ("autoload_observed_across_reboot", "soak_tested",
                      "driver_reload_tested"):
            if wifi.get(field) is not False:
                errors.append(f"{path}: Ubuntu Wi-Fi {field} is overstated")
        if wifi.get("taint_added_by_load") != 4096:
            errors.append(f"{path}: Ubuntu Wi-Fi load must add only the out-of-tree taint")
        if data.get("latest_authenticated_working_run") != 17:
            errors.append(f"{path}: latest authenticated working run must be 17")

    boot_media = data.get("boot_media")
    if not isinstance(boot_media, dict):
        errors.append(f"{path}: boot_media is not an object")
    else:
        if boot_media.get("run") != 15:
            errors.append(f"{path}: boot_media must identify Run 15")
        if boot_media.get("distribution") != "CachyOS":
            errors.append(f"{path}: boot_media must identify CachyOS")
        if boot_media.get("physical_usb_boot_partition_verified") is not True:
            errors.append(f"{path}: physical USB boot partition is not verified")
        if boot_media.get("fat_verify_result") != "pass":
            errors.append(f"{path}: physical USB FAT verification did not pass")
        if boot_media.get("linux_root_partition_directly_inspected_on_macos") is not False:
            errors.append(f"{path}: Linux root inspection scope is overstated")
        for name in ("bzimage", "initrd", "cmdline", "vram", "kexec"):
            artifact = boot_media.get(name)
            if not isinstance(artifact, dict):
                errors.append(f"{path}: boot media {name} is not an object")
                continue
            digest = artifact.get("sha256", "")
            if not isinstance(digest, str) or not SHA256.fullmatch(digest):
                errors.append(f"{path}: invalid boot media {name} SHA-256")
            size = artifact.get("size")
            if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
                errors.append(f"{path}: invalid boot media {name} size")

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
