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
                "ps5_pro_linux_test3",
                "ubuntu_control", "ubuntu_wifi", "dma_e820_build",
                "ubuntu_ci_dma_run", "cachyos_k73_run", "boot_media", "artifacts",
                "latest_authenticated_working_run",
                "latest_authenticated_working_run_scope", "latest_tested_run",
                "last_observed_marker", "current_boundary"):
        if key not in data:
            errors.append(f"{path}: missing {key}")

    checkpoints = data.get("checkpoints", {})
    if data.get("console_model") != "regular-and-pro":
        errors.append(f"{path}: console_model must include regular and Pro results")
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

    pro = data.get("ps5_pro_linux_test3")
    if not isinstance(pro, dict):
        errors.append(f"{path}: ps5_pro_linux_test3 is not an object")
    else:
        expected = {
            "hardware_test_date": "2026-10-24",
            "loader_release_tag": "firmware-11.60-pro-linux-test-3",
            "loader_release_url": (
                "https://github.com/gzimbric/ps5-linux-loader/releases/tag/"
                "firmware-11.60-pro-linux-test-3"
            ),
            "image_release_tag": "ubuntu2404-k73-image-3",
            "image_release_url": (
                "https://github.com/gzimbric/ps5-linux-image/releases/tag/"
                "ubuntu2404-k73-image-3"
            ),
            "released_image_unchanged": True,
            "console_count": 1,
            "cold_boots_with_visible_hdmi": 2,
            "display_resolution": "1920x1080",
            "authenticated_wired_ssh": True,
            "onboard_wifi_working": True,
            "usb_input_working_with_autosuspend_disabled": True,
            "required_kernel_option": "usbcore.autosuspend=-1",
            "bluetooth_working": False,
            "pro_frequency_control_tested": False,
            "gpu_temperature_available": False,
            "games_tested": False,
            "boot_report_service_passed": False,
            "regular_console_hardware_tested_with_this_image": False,
        }
        for key, value in expected.items():
            if pro.get(key) != value:
                errors.append(f"{path}: unexpected PS5 Pro Test 3 {key}")
        for key in ("loader_source_commit", "image_source_commit"):
            value = pro.get(key, "")
            if not isinstance(value, str) or not GIT_COMMIT.fullmatch(value):
                errors.append(f"{path}: invalid PS5 Pro Test 3 {key}")
        if pro.get("loader_source_commit") != (
                "aff37e0f83dc09106fb4196221b3d7a52928031a"):
            errors.append(f"{path}: unexpected PS5 Pro Test 3 loader source")
        if pro.get("image_source_commit") != (
                "27e49914b41f2143354f1579353af6c1ffc2ada9"):
            errors.append(f"{path}: unexpected PS5 Pro Test 3 image source")

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

    dma = data.get("dma_e820_build")
    if not isinstance(dma, dict):
        errors.append(f"{path}: dma_e820_build is not an object")
    else:
        if dma.get("run") != 18:
            errors.append(f"{path}: DMA E820 build test must be Run 18")
        if dma.get("result") != "pass-authenticated-wired-ssh-reserved-map-usb-io-check":
            errors.append(f"{path}: unexpected Run 18 result")
        if dma.get("distribution") != "CachyOS":
            errors.append(f"{path}: Run 18 must identify CachyOS")
        if dma.get("same_console_as_run15") is not True:
            errors.append(f"{path}: Run 18 must record same-console scope")
        if dma.get("release_loader_baseline") is not False:
            errors.append(f"{path}: Run 18 DMA build must not replace the Run 15 release baseline")
        loader = dma.get("loader", {})
        if not isinstance(loader, dict):
            loader = {}
            errors.append(f"{path}: Run 18 DMA loader is not an object")
        if loader.get("size") != 169872:
            errors.append(f"{path}: unexpected Run 18 DMA loader size")
        if loader.get("sha256") != (
            "2e1758a2d013305bcb9faa0eb3adf18c34ed76ad85313dd945719c8bf2a0c9c0"
        ):
            errors.append(f"{path}: unexpected Run 18 DMA loader SHA-256")
        if loader.get("byte_identical_to_run15") is not False:
            errors.append(f"{path}: Run 18 DMA loader must differ from Run 15")
        if loader.get("output_byte_identical_to_run16") is not True:
            errors.append(f"{path}: Run 18 DMA loader output must match Run 16")
        if loader.get("upstream_reservation_commit") != "8cda4c1":
            errors.append(f"{path}: unexpected Run 18 upstream reservation commit")
        if loader.get("included") is not False:
            errors.append(f"{path}: Run 18 DMA loader binary must not be included")
        expected_map = {
            "low_ram": {"start": "0x00100000", "end_exclusive": "0x01000000"},
            "reserved": {"start": "0x01000000", "end_exclusive": "0x40000000"},
        }
        for name, expected in expected_map.items():
            if loader.get(name) != expected:
                errors.append(f"{path}: unexpected Run 18 DMA loader {name} range")
        release = display.get("release") if isinstance(display, dict) else None
        if (isinstance(release, dict) and
                release.get("elf_sha256") == loader.get("sha256")):
            errors.append(f"{path}: Run 15 must remain the release loader ELF")
        expected_boot_files = {
            "bzimage": (12702720, "11280a8f5ca197ee5458fd446a4dadf2d0b5d0ef6218583cbe6325ee34e99cde"),
            "initrd": (54376639, "c37b88569ef8f05b0b4ae432a8ec0fd323b7a3537a6441f8c45baaad45ff061f"),
            "cmdline": (118, "aec7a85e9ebcf36e4bdaeb89242b898e17817acd40c16db57a3bb9c3117b1da8"),
            "vram": (11, "bc4642feb06a4cc6d10d5865e321efaad7ab3f3f1d5d025151b79978164310a0"),
        }
        boot_files = dma.get("boot_files", {})
        for name, (size, digest) in expected_boot_files.items():
            artifact = boot_files.get(name) if isinstance(boot_files, dict) else None
            if not isinstance(artifact, dict):
                errors.append(f"{path}: Run 18 boot file {name} is not an object")
                continue
            if artifact.get("size") != size:
                errors.append(f"{path}: unexpected Run 18 boot file {name} size")
            if artifact.get("sha256") != digest:
                errors.append(f"{path}: unexpected Run 18 boot file {name} SHA-256")
        disk_image = dma.get("disk_image", {})
        if not isinstance(disk_image, dict) or disk_image.get("included") is not False:
            errors.append(f"{path}: Run 18 disk image must not be included")
        observed = dma.get("observed_e820", {})
        reserved = observed.get("reserved") if isinstance(observed, dict) else None
        expected_reserved = {
            "start": "0x0000000001000000",
            "end_inclusive": "0x000000003fffffff",
            "type": "device reserved",
        }
        if reserved != expected_reserved:
            errors.append(f"{path}: unexpected Run 18 observed e820 reserved range")
        else:
            try:
                matches = (
                    int(reserved["start"], 16) ==
                    int(loader.get("reserved", {}).get("start", ""), 16) and
                    int(reserved["end_inclusive"], 16) + 1 ==
                    int(loader.get("reserved", {}).get("end_exclusive", ""), 16)
                )
            except (AttributeError, TypeError, ValueError):
                matches = False
            if not matches:
                errors.append(
                    f"{path}: Run 18 observed e820 reservation disagrees with the loader map")
        if dma.get("mem_total_kib") != 14783608:
            errors.append(f"{path}: unexpected Run 18 mem_total_kib")
        io_check = dma.get("io_check", {})
        if not isinstance(io_check, dict):
            io_check = {}
            errors.append(f"{path}: Run 18 io_check is not an object")
        if io_check.get("result") != "pass":
            errors.append(f"{path}: unexpected Run 18 I/O check result")
        files = io_check.get("files")
        file_size = io_check.get("file_size_bytes")
        written = io_check.get("bytes_written")
        if (not all(isinstance(value, int) and not isinstance(value, bool)
                    for value in (files, file_size, written)) or
                files != 3 or files * file_size != written):
            errors.append(f"{path}: inconsistent Run 18 I/O check size")
        if io_check.get("caches_dropped") is not True:
            errors.append(f"{path}: Run 18 I/O check must drop caches before re-reading")
        if io_check.get("sha256_matched") is not True:
            errors.append(f"{path}: Run 18 I/O check hashes must match")
        for field in ("independent_hardware_reproduction", "ab_control_run",
                      "tester_errors_reproduced", "soak_tested",
                      "physical_display_observed", "ubuntu_ci_image_tested"):
            if dma.get(field) is not False:
                errors.append(f"{path}: Run 18 {field} is overstated")
        display_state = dma.get("display", {})
        if (not isinstance(display_state, dict) or
                display_state.get("direct_operator_observation") is not False):
            errors.append(f"{path}: Run 18 display observation is overstated")
        dma_wifi = dma.get("wifi", {})
        if (not isinstance(dma_wifi, dict) or
                dma_wifi.get("autoload_observed_across_reboot") is not False):
            errors.append(f"{path}: Run 18 Wi-Fi autoload across reboot is overstated")

    tester_run = data.get("ubuntu_ci_dma_run")
    if not isinstance(tester_run, dict):
        errors.append(f"{path}: ubuntu_ci_dma_run is not an object")
    else:
        if tester_run.get("run") != 19:
            errors.append(f"{path}: CI Ubuntu and DMA loader test must be Run 19")
        if tester_run.get("result") != (
            "pass-physical-display-authenticated-wired-ssh-reserved-map-tester-guide-checks"
        ):
            errors.append(f"{path}: unexpected Run 19 result")
        if tester_run.get("same_console_as_run15") is not True:
            errors.append(f"{path}: Run 19 must record same-console scope")
        if tester_run.get("release_loader_baseline") is not False:
            errors.append(f"{path}: Run 19 must not replace the Run 15 release baseline")
        image = tester_run.get("image", {})
        if not isinstance(image, dict):
            image = {}
            errors.append(f"{path}: Run 19 image is not an object")
        if image.get("release_tag") != "ubuntu2404-1160-build-3":
            errors.append(f"{path}: unexpected Run 19 image release tag")
        source_commit = image.get("source_commit", "")
        if not isinstance(source_commit, str) or not GIT_COMMIT.fullmatch(source_commit):
            errors.append(f"{path}: invalid Run 19 image source commit")
        raw = image.get("raw", {})
        if not isinstance(raw, dict):
            raw = {}
        if raw.get("size") != 16777216000:
            errors.append(f"{path}: unexpected Run 19 image size")
        if raw.get("sha256") != (
            "cb01a4f53dedc390a07cdcd42b93dda0762e0c4dee8efe0130af7bdb36ba7fda"
        ):
            errors.append(f"{path}: unexpected Run 19 image SHA-256")
        for name in ("xz", "kernel_package"):
            entry = image.get(name)
            digest = entry.get("sha256", "") if isinstance(entry, dict) else ""
            if not isinstance(digest, str) or not SHA256.fullmatch(digest):
                errors.append(f"{path}: invalid Run 19 image {name} SHA-256")
        if image.get("included") is not False:
            errors.append(f"{path}: Run 19 disk image must not be included")
        loader = tester_run.get("loader", {})
        if not isinstance(loader, dict):
            loader = {}
            errors.append(f"{path}: Run 19 loader is not an object")
        if loader.get("size") != 169872:
            errors.append(f"{path}: unexpected Run 19 loader size")
        if loader.get("sha256") != (
            "2e1758a2d013305bcb9faa0eb3adf18c34ed76ad85313dd945719c8bf2a0c9c0"
        ):
            errors.append(f"{path}: unexpected Run 19 loader SHA-256")
        dma_loader = dma.get("loader") if isinstance(dma, dict) else None
        if (not isinstance(dma_loader, dict) or
                dma_loader.get("sha256") != loader.get("sha256")):
            errors.append(f"{path}: Run 19 loader must be the Run 18 DMA loader")
        if loader.get("release_tag") != "firmware-11.60-dma-e820-run18":
            errors.append(f"{path}: unexpected Run 19 loader release tag")
        if loader.get("output_byte_identical_to_run18") is not True:
            errors.append(f"{path}: Run 19 loader output must match Run 18")
        if loader.get("included") is not False:
            errors.append(f"{path}: Run 19 loader binary must not be included")
        release = display.get("release") if isinstance(display, dict) else None
        if (isinstance(release, dict) and
                release.get("elf_sha256") == loader.get("sha256")):
            errors.append(f"{path}: Run 15 must remain the release loader ELF")
        expected_boot_files = {
            "bzimage": (12702720, "11280a8f5ca197ee5458fd446a4dadf2d0b5d0ef6218583cbe6325ee34e99cde"),
            "initrd": (54376639, None),
            "cmdline": (121, "6b3c09112fe049d3cbeada65fb3c82bb0f5fcaddce6c0709051df3d9f5a79f6d"),
            "vram": (11, "bc4642feb06a4cc6d10d5865e321efaad7ab3f3f1d5d025151b79978164310a0"),
            "kexec": (136, "0f26e09911a8a2bc9912d7c77fee6ac09ccd18a820086cb103be92de081b6c52"),
        }
        boot_files = tester_run.get("boot_files", {})
        for name, (size, digest) in expected_boot_files.items():
            artifact = boot_files.get(name) if isinstance(boot_files, dict) else None
            if not isinstance(artifact, dict):
                errors.append(f"{path}: Run 19 boot file {name} is not an object")
                continue
            if artifact.get("size") != size:
                errors.append(f"{path}: unexpected Run 19 boot file {name} size")
            actual = artifact.get("sha256", "")
            if digest is None:
                if not isinstance(actual, str) or not SHA256.fullmatch(actual):
                    errors.append(f"{path}: invalid Run 19 boot file {name} SHA-256")
            elif actual != digest:
                errors.append(f"{path}: unexpected Run 19 boot file {name} SHA-256")
        observed = tester_run.get("observed_e820", {})
        reserved = observed.get("reserved") if isinstance(observed, dict) else None
        if reserved != {
            "start": "0x0000000001000000",
            "end_inclusive": "0x000000003fffffff",
            "type": "device reserved",
        }:
            errors.append(f"{path}: unexpected Run 19 observed e820 reserved range")
        if tester_run.get("mem_total_kib") != 14783608:
            errors.append(f"{path}: unexpected Run 19 mem_total_kib")
        checks = tester_run.get("tester_guide_checks", {})
        io_check = checks.get("io_check") if isinstance(checks, dict) else None
        if not isinstance(io_check, dict):
            io_check = {}
            errors.append(f"{path}: Run 19 tester guide I/O check is not an object")
        if io_check.get("result") != "pass":
            errors.append(f"{path}: unexpected Run 19 I/O check result")
        files = io_check.get("files")
        file_size = io_check.get("file_size_bytes")
        written = io_check.get("bytes_written")
        if (not all(isinstance(value, int) and not isinstance(value, bool)
                    for value in (files, file_size, written)) or
                files != 3 or files * file_size != written):
            errors.append(f"{path}: inconsistent Run 19 I/O check size")
        if io_check.get("caches_dropped") is not True:
            errors.append(f"{path}: Run 19 I/O check must drop caches before re-reading")
        if io_check.get("sha256_matched") is not True:
            errors.append(f"{path}: Run 19 I/O check hashes must match")
        if io_check.get("script_sha256") != (
            "7bc68fa14c1875cb07b9dde5c00c95edec2b1d1d441ff756ffd929bfb720aa52"
        ):
            errors.append(f"{path}: unexpected Run 19 I/O check script SHA-256")
        display_state = tester_run.get("display", {})
        if (tester_run.get("physical_display_observed") is not True or
                not isinstance(display_state, dict) or
                display_state.get("direct_operator_observation") is not True):
            errors.append(f"{path}: Run 19 must record the directly observed display")
        for field in ("independent_hardware_reproduction", "ab_control_run",
                      "tester_errors_reproduced", "soak_tested", "wifi_tested"):
            if tester_run.get(field) is not False:
                errors.append(f"{path}: Run 19 {field} is overstated")

    k73 = data.get("cachyos_k73_run")
    if not isinstance(k73, dict):
        errors.append(f"{path}: cachyos_k73_run is not an object")
    else:
        if k73.get("run") != 21:
            errors.append(f"{path}: CachyOS 7.3 and bounded Wi-Fi loader test must be Run 21")
        if k73.get("result") != (
            "pass-physical-display-authenticated-wired-ssh-reserved-map-wifi-join"
        ):
            errors.append(f"{path}: unexpected Run 21 result")
        if k73.get("same_console_as_run15") is not True:
            errors.append(f"{path}: Run 21 must record same-console scope")
        if k73.get("release_loader_baseline") is not False:
            errors.append(f"{path}: Run 21 must not replace the Run 15 release baseline")
        upstream = k73.get("upstream_kernel_work", {})
        if (not isinstance(upstream, dict) or
                upstream.get("author") != "rmux" or
                upstream.get("repository") != "https://github.com/rmuxnet/ps5-linux-patches-1"):
            errors.append(f"{path}: Run 21 must credit rmux for the 7.3 port and frequency drivers")
        kernel = k73.get("kernel", {})
        if not isinstance(kernel, dict):
            kernel = {}
            errors.append(f"{path}: Run 21 kernel is not an object")
        if kernel.get("version") != "7.3.0":
            errors.append(f"{path}: unexpected Run 21 kernel version")
        patch_commit = kernel.get("patch_commit", "")
        if (not isinstance(patch_commit, str) or not GIT_COMMIT.fullmatch(patch_commit) or
                not isinstance(upstream, dict) or upstream.get("commit") != patch_commit or
                not patch_commit.startswith("36f173f")):
            errors.append(f"{path}: unexpected Run 21 kernel patch commit")
        image = k73.get("image", {})
        if not isinstance(image, dict):
            image = {}
            errors.append(f"{path}: Run 21 image is not an object")
        if image.get("source_branch") != "cachyos-1160-k73":
            errors.append(f"{path}: unexpected Run 21 image source branch")
        if image.get("built_by_ci") is not False or k73.get("ci_built_image") is not False:
            errors.append(f"{path}: Run 21 booted a local image build, not a CI build")
        raw = image.get("raw", {})
        if not isinstance(raw, dict):
            raw = {}
        if raw.get("size") != 12582912000:
            errors.append(f"{path}: unexpected Run 21 image size")
        if raw.get("sha256") != (
            "d593bb5d52c9054d8e3671d6b67fae0687aa239cb3d104a503999e6a5906789d"
        ):
            errors.append(f"{path}: unexpected Run 21 image SHA-256")
        if image.get("included") is not False:
            errors.append(f"{path}: Run 21 disk image must not be included")
        later_ci = k73.get("later_ci_build", {})
        if (not isinstance(later_ci, dict) or
                later_ci.get("release_tag") != "cachyos1160-k73-image-1" or
                later_ci.get("workflow_conclusion") != "success" or
                later_ci.get("draft_release_created") is not True or
                later_ci.get("booted") is not False or
                later_ci.get("superseded_by") != "cachyos1160-k73-image-2"):
            errors.append(f"{path}: Run 21 later CI build boot is overstated")
        ci_build_2 = k73.get("ci_build_2", {})
        if not isinstance(ci_build_2, dict):
            ci_build_2 = {}
            errors.append(f"{path}: CachyOS image 2 record is not an object")
        if (ci_build_2.get("release_tag") != "cachyos1160-k73-image-2" or
                ci_build_2.get("source_commit") !=
                "346088a48f66eb956dafdec9de5085e73b2d44a5" or
                ci_build_2.get("workflow_run") != 39481460775):
            errors.append(f"{path}: unexpected CachyOS image 2 source identity")
        if (ci_build_2.get("workflow_conclusion") != "success" or
                ci_build_2.get("ci_result_verified") is not True):
            errors.append(
                f"{path}: CachyOS image 2 CI result is not the verified success")
        if (ci_build_2.get("release_url") !=
                "https://github.com/gzimbric/ps5-linux-image/releases/tag/cachyos1160-k73-image-2" or
                ci_build_2.get("release_policy") !=
                "public-prerelease-for-hardware-testing" or
                ci_build_2.get("draft_release_created") is not True or
                ci_build_2.get("release_is_draft") is not False or
                ci_build_2.get("release_is_prerelease") is not True or
                ci_build_2.get("published_for_testing") is not True or
                ci_build_2.get("booted") is not False):
            errors.append(
                f"{path}: CachyOS image 2 prerelease or boot state is overstated")
        package = ci_build_2.get("kernel_package", {})
        if (not isinstance(package, dict) or
                package.get("name") != "linux-ps5" or
                package.get("version") != "7.3.0-2" or
                package.get("kbuild_build_version") != 2):
            errors.append(f"{path}: unexpected CachyOS image 2 kernel package identity")
        build2_base = ci_build_2.get("base_patch_set", {})
        if (not isinstance(build2_base, dict) or
                build2_base.get("repository") !=
                "https://github.com/rmuxnet/ps5-linux-patches-1" or
                build2_base.get("commit") != patch_commit or
                build2_base.get("used_as_published") is not True):
            errors.append(f"{path}: CachyOS image 2 must use the pinned rmux base patch")
        bt_followup = ci_build_2.get("bluetooth_followup_patch", {})
        if (not isinstance(bt_followup, dict) or
                bt_followup.get("sha256") !=
                "54d7addbb4cd95c943f9a4485229ac5516ad08ebe0f4aa02fd72cf33298fa0a2" or
                bt_followup.get("applied_after_rmux_base") is not True or
                bt_followup.get("hardware_tested") is not False):
            errors.append(f"{path}: unexpected CachyOS image 2 Bluetooth follow-up")
        external_bt = bt_followup.get("external_confirmation", {})
        if (not isinstance(external_bt, dict) or
                external_bt.get("repository") !=
                "https://github.com/VivaLaVent/ps5-bazzite-deck" or
                external_bt.get("release_tag") != "v1.0.3" or
                external_bt.get("source_commit") !=
                "807d5bcaa834f574f6d927703ff95c1caffc96ba" or
                external_bt.get("patch_sha256") !=
                "c01bdcc134f25a86825f2824d12a82da02db18e7b1940db722223b0c4611eed8" or
                external_bt.get("firmware") != "13.60" or
                external_bt.get("console_model") != "CFI-10xx" or
                external_bt.get("same_core_fix") is not True or
                external_bt.get("byte_identical_patch") is not False or
                external_bt.get("image2_hardware_test") is not False):
            errors.append(f"{path}: unexpected image 2 Bluetooth external confirmation")
        expected_build2_changes = [
            "IW620 Bluetooth quirk ordering follow-up after the rmux 7.3 base patch",
            "IW620 firmware-before-explicit-driver-load ordering",
            "linux-ps5 7.3.0-2 package identity with KBUILD_BUILD_VERSION=2",
            "CPU and GPU frequency drivers remain manual-only",
            "ps5fan.service enabled by default with fixed maximum servo pattern 3",
        ]
        expected_build2_unresolved = [
            "Steam Switch to Desktop hangs because the image's steamos-session-select is not run and the next-session token stays gamescope",
            "joining Wi-Fi from the KDE network menu fails with the access point not in the scan list",
        ]
        if ci_build_2.get("included_in_source") != expected_build2_changes:
            errors.append(f"{path}: unexpected CachyOS image 2 source changes")
        if ci_build_2.get("unresolved_image_behaviors") != expected_build2_unresolved:
            errors.append(f"{path}: unexpected CachyOS image 2 unresolved behaviors")
        fan_policy = ci_build_2.get("fan_policy", {})
        if fan_policy != {
            "service": "ps5fan.service",
            "enabled_by_default": True,
            "servo_pattern": 3,
            "requested_setting": "tested-maximum-bring-up-setting",
            "dynamic_temperature_curve": False,
            "rpm_telemetry": False,
        }:
            errors.append(f"{path}: unexpected CachyOS image 2 fan policy")
        asset_policy = ci_build_2.get("release_asset_policy", {})
        if (not isinstance(asset_policy, dict) or
                asset_policy.get("format") != "single-img-xz" or
                asset_policy.get("expected_image_asset_count") != 1 or
                asset_policy.get("maximum_size_bytes_exclusive") != 2147483648 or
                asset_policy.get("fail_instead_of_split") is not True):
            errors.append(f"{path}: CachyOS image 2 must be one unsplit .img.xz")
        elif (asset_policy.get("asset_name") !=
              "ps5-cachyos1160-k73.img.xz" or
              asset_policy.get("size") != 1943471712 or
              asset_policy.get("sha256") !=
              "8b785243f79a32a4155cc1e39bed01d580e25ca514e88abbfed1a8a8157a281a" or
              asset_policy.get("verified") is not True):
            errors.append(
                f"{path}: unexpected CachyOS image 2 release asset identity")
        raw_image = ci_build_2.get("raw_image", {})
        if (not isinstance(raw_image, dict) or
                raw_image.get("name") != "ps5-cachyos1160-k73.img" or
                raw_image.get("size") != 12582912000 or
                raw_image.get("sha256") !=
                "3798c7dba96412c5301eb201d8bf8aa4edd1b2f80a743dfd7b90b2a79222c62d" or
                raw_image.get("verified") is not True):
            errors.append(
                f"{path}: unexpected CachyOS image 2 raw image identity")
        loader = k73.get("loader", {})
        if not isinstance(loader, dict):
            loader = {}
            errors.append(f"{path}: Run 21 loader is not an object")
        if loader.get("size") != 170904:
            errors.append(f"{path}: unexpected Run 21 loader size")
        if loader.get("sha256") != (
            "e9fe6469943e97a635eccd3f674e55876b56cd1bbd69023eee3af4acea3a1b5f"
        ):
            errors.append(f"{path}: unexpected Run 21 loader SHA-256")
        if loader.get("source_commit") != "98925a2561ad43769a7a7445a0bd957b24e84073":
            errors.append(f"{path}: unexpected Run 21 loader source commit")
        if loader.get("build_target") != "linux-1160-dma-e820-bounded-wifi":
            errors.append(f"{path}: unexpected Run 21 loader build target")
        if (loader.get("release_tag") !=
                "firmware-11.60-dma-e820-bounded-run21" or
                loader.get("release_url") !=
                "https://github.com/gzimbric/ps5-linux-loader/releases/tag/firmware-11.60-dma-e820-bounded-run21" or
                loader.get("release_policy") !=
                "public-prerelease-for-hardware-testing" or
                loader.get("release_is_draft") is not False or
                loader.get("release_is_prerelease") is not True or
                loader.get("published_for_testing") is not True or
                loader.get("release_also_holds_unbooted_bounded_elf") is not True):
            errors.append(f"{path}: unexpected Run 21 loader prerelease state")
        loader_assets = loader.get("release_assets", {})
        bounded_wifi_asset = (loader_assets.get("bounded_wifi", {})
                              if isinstance(loader_assets, dict) else {})
        if bounded_wifi_asset != {
            "name": "ps5-linux-loader-1160-dma-e820-bounded-wifi.elf",
            "size": 170904,
            "sha256": "e9fe6469943e97a635eccd3f674e55876b56cd1bbd69023eee3af4acea3a1b5f",
            "hardware_booted": True,
            "booted_with_exact_ci_image_2": False,
        }:
            errors.append(f"{path}: unexpected bounded Wi-Fi release asset")
        bounded_non_wifi_asset = (loader_assets.get("bounded_non_wifi", {})
                                  if isinstance(loader_assets, dict) else {})
        if bounded_non_wifi_asset != {
            "name": "ps5-linux-loader-1160-dma-e820-bounded.elf",
            "size": 170904,
            "sha256": "1c80b040c5a808b3f09418728424a875d5598fe6b2a5d68adeb4db5979a7541a",
            "hardware_booted": False,
        }:
            errors.append(f"{path}: unexpected bounded non-Wi-Fi release asset")
        if loader.get("included") is not False:
            errors.append(f"{path}: Run 21 loader binary must not be included")
        release = display.get("release") if isinstance(display, dict) else None
        if (isinstance(release, dict) and
                release.get("elf_sha256") == loader.get("sha256")):
            errors.append(f"{path}: Run 15 must remain the release loader ELF")
        dma_loader = dma.get("loader") if isinstance(dma, dict) else None
        if isinstance(dma_loader, dict) and dma_loader.get("sha256") == loader.get("sha256"):
            errors.append(f"{path}: Run 21 loader must differ from the Run 18 DMA loader")
        if loader.get("sends_recorded") != 1 or loader.get("bytes_sent") != loader.get("size"):
            errors.append(f"{path}: Run 21 loader send must be one full ELF")
        if loader.get("output_bytes") != 3035:
            errors.append(f"{path}: unexpected Run 21 loader output size")
        wifi = k73.get("wifi", {})
        if not isinstance(wifi, dict):
            wifi = {}
            errors.append(f"{path}: Run 21 Wi-Fi is not an object")
        wifi_firmware = wifi.get("firmware", {})
        if not isinstance(wifi_firmware, dict):
            wifi_firmware = {}
        run17_wifi = data.get("ubuntu_wifi", {})
        run17_firmware = run17_wifi.get("firmware", {}) if isinstance(run17_wifi, dict) else {}
        if not isinstance(run17_firmware, dict):
            run17_firmware = {}
        dump = loader.get("wifi_firmware_dump", {})
        if (not isinstance(dump, dict) or dump.get("bytes") != 498108 or
                dump.get("bytes") != wifi_firmware.get("size") or
                dump.get("bytes") != run17_firmware.get("size")):
            errors.append(f"{path}: Run 21 loader Wi-Fi firmware dump size disagrees")
        if (wifi_firmware.get("sha256") !=
                "eafef24af118f96f84a652e17aeed555ec4ac719b9fac11ff98a2de7e2b4b369" or
                wifi_firmware.get("sha256") != run17_firmware.get("sha256")):
            errors.append(f"{path}: Run 21 Wi-Fi firmware must be the Run 17 p47 blob")
        if wifi_firmware.get("included") is not False:
            errors.append(f"{path}: Run 21 Wi-Fi firmware must not be included")
        wake_copy = loader.get("wake_copy", {})
        if not isinstance(wake_copy, dict):
            wake_copy = {}
        window = wake_copy.get("proven_window", {})
        if not isinstance(window, dict):
            window = {}
        try:
            inside = (
                int(window["start"], 16) <= int(wake_copy["start"], 16) <
                int(wake_copy["end"], 16) <= int(window["end_exclusive"], 16)
            )
        except (KeyError, TypeError, ValueError):
            inside = False
        if not inside or wake_copy.get("inside_proven_window") is not True:
            errors.append(f"{path}: Run 21 wake copy must stay inside the proven window")
        if window != {"start": "0x100000000", "end_exclusive": "0x1040048c0"}:
            errors.append(f"{path}: unexpected Run 21 proven wake copy window")
        expected_boot_files = {
            "bzimage": (11613184, "db8617da59ffe196fd2e6f9ef5a1a3872f77eaca7189858a395c91112b6629a7"),
            "initrd": (51900862, "56a8a0b91cfa46d4f666aba89055ec6621b3c86708c7b0c28ccf09ac23aa9bbc"),
            "cmdline": (118, "aec7a85e9ebcf36e4bdaeb89242b898e17817acd40c16db57a3bb9c3117b1da8"),
            "vram": (11, "bc4642feb06a4cc6d10d5865e321efaad7ab3f3f1d5d025151b79978164310a0"),
            "kexec": (136, "0f26e09911a8a2bc9912d7c77fee6ac09ccd18a820086cb103be92de081b6c52"),
        }
        boot_files = k73.get("boot_files", {})
        for name, (size, digest) in expected_boot_files.items():
            artifact = boot_files.get(name) if isinstance(boot_files, dict) else None
            if not isinstance(artifact, dict):
                errors.append(f"{path}: Run 21 boot file {name} is not an object")
                continue
            if artifact.get("size") != size:
                errors.append(f"{path}: unexpected Run 21 boot file {name} size")
            if artifact.get("sha256") != digest:
                errors.append(f"{path}: unexpected Run 21 boot file {name} SHA-256")
        wake = k73.get("wake", {})
        if not isinstance(wake, dict):
            wake = {}
        for field in ("seconds_elf_send_to_wake", "seconds_wake_to_tcp22"):
            value = wake.get(field)
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                errors.append(f"{path}: invalid Run 21 wake timing {field}")
        observed = k73.get("observed_e820", {})
        reserved = observed.get("reserved") if isinstance(observed, dict) else None
        expected_reserved = {
            "start": "0x0000000001000000",
            "end_inclusive": "0x000000003fffffff",
            "type": "device reserved",
        }
        if reserved != expected_reserved:
            errors.append(f"{path}: unexpected Run 21 observed e820 reserved range")
        kaslr = k73.get("kaslr", {})
        if not isinstance(kaslr, dict):
            kaslr = {}
        if kaslr.get("kernel_code_physical_start") != "0x26ec00000":
            errors.append(f"{path}: unexpected Run 21 KASLR kernel physical start")
        try:
            above = (int(kaslr["kernel_code_physical_start"], 16) >
                     int(expected_reserved["end_inclusive"], 16))
        except (KeyError, TypeError, ValueError):
            above = False
        if not above or kaslr.get("above_reserved_range") is not True:
            errors.append(f"{path}: Run 21 kernel must sit above the reserved range")
        if k73.get("mem_total_kib") != 14788356:
            errors.append(f"{path}: unexpected Run 21 mem_total_kib")
        display_state = k73.get("display", {})
        if (k73.get("physical_display_observed") is not True or
                not isinstance(display_state, dict) or
                display_state.get("direct_operator_observation") is not True):
            errors.append(f"{path}: Run 21 must record the directly observed display")
        vcn = k73.get("vcn", {})
        if (not isinstance(vcn, dict) or vcn.get("vcn_initialized") is not True or
                vcn.get("decode_tested") is not False):
            errors.append(f"{path}: Run 21 VCN must be initialized with decode not tested")
        association = wifi.get("association", {})
        download = wifi.get("download", {})
        if (wifi.get("joined") is not True or not isinstance(association, dict) or
                association.get("band") != "5GHz" or not isinstance(download, dict) or
                download.get("bound_to_wifi_interface") is not True or
                download.get("bytes_per_second") != 23979239):
            errors.append(f"{path}: unexpected Run 21 Wi-Fi join or speed")
        if k73.get("bluetooth_working") is not False:
            errors.append(f"{path}: Run 21 Bluetooth is overstated")
        if k73.get("dualsense_usb") is not True:
            errors.append(f"{path}: Run 21 must record the DualSense over USB")
        thermal = k73.get("thermal", {})
        if not isinstance(thermal, dict):
            thermal = {}
        steps = thermal.get("steps")
        expected_steps = {
            "linux-7.3-no-frequency-drivers": [49.5, 50.25],
            "plus-ps5_gpufreq": [35.75, 36.5],
            "plus-ps5_cpufreq": [35.5, 36.5],
        }
        if (not isinstance(steps, list) or
                any(not isinstance(step, dict) or not isinstance(step.get("name"), str)
                    for step in steps) or
                {step["name"]: step.get("settled_c") for step in steps} != expected_steps):
            errors.append(f"{path}: unexpected Run 21 thermal steps")
        if thermal.get("frequency_drivers_autoloaded") is not False:
            errors.append(f"{path}: Run 21 frequency driver autoload is overstated")

        install = k73.get("large_install_observation", {})
        if not isinstance(install, dict):
            install = {}
        expected_install = {
            "steam_update_result": "finished-no-error",
            "download_bytes": 53229366208,
            "staged_bytes": 59880080270,
            "committed_files": 347,
            "steam_staged_verification_observed": True,
            "manual_steam_integrity_check": False,
            "independent_readback_or_hash_check": False,
        }
        if any(install.get(key) != value for key, value in expected_install.items()):
            errors.append(f"{path}: unexpected Run 21 large-install observation")
        watcher = install.get("watcher", {})
        expected_watcher = {
            "samples": 480,
            "duration_seconds": 14393,
            "root_free_start_gib_displayed": 213,
            "root_free_end_gib_displayed": 159,
            "storage_error_lines_per_sample": 0,
            "throughput_and_total_counters_valid": False,
            "diskstats_fields_used": [7, 11],
            "diskstats_sector_fields_required": [6, 10],
        }
        if (not isinstance(watcher, dict) or
                any(watcher.get(key) != value
                    for key, value in expected_watcher.items())):
            errors.append(f"{path}: unexpected Run 21 storage-watcher observation")

        game_load = k73.get("game_load_observation", {})
        expected_game_load = {
            "sample_seconds": 5,
            "samples": 540,
            "game_thread_samples": 88,
            "gpu_peak_mhz": 2230,
            "gpu_peak_samples": 76,
            "gpu_peak_trans_stat_ms": 386159,
            "temperature_min_c": 35.0,
            "temperature_peak_c": 84.0,
            "samples_at_or_above_80_c": 30,
            "gpu_or_iommu_error_lines": 0,
            "logger_ended_while_load_active": True,
            "operator_confirmed_gameplay": False,
            "operator_confirmed_display_during_load": False,
            "thermal_equilibrium_established": False,
            "stability_established": False,
        }
        if (not isinstance(game_load, dict) or
                any(game_load.get(key) != value
                    for key, value in expected_game_load.items())):
            errors.append(f"{path}: unexpected Run 21 game-load observation")
        if k73.get("game_load_telemetry_recorded") is not True:
            errors.append(f"{path}: Run 21 game-load telemetry is missing")

        pending = k73.get("pending")
        expected_pending = [
            "operator-run Steam Verify integrity of game files",
            "independent read-back or hash verification of the installed files",
            "operator-observed gameplay and display with a bounded thermal and stability run",
        ]
        if pending != expected_pending:
            errors.append(f"{path}: Run 21 must list the three remaining checks")
        followup = k73.get("post_run21_image_followup", {})
        if (not isinstance(followup, dict) or
                followup.get("included_in_ci_build_2_source") !=
                expected_build2_changes or
                followup.get("unresolved_after_ci_build_2_source") !=
                expected_build2_unresolved):
            errors.append(
                f"{path}: Run 21 follow-up must separate image 2 changes from unresolved behavior")
        for field in ("independent_hardware_reproduction", "ab_control_run",
                      "tester_errors_reproduced", "soak_tested", "gaming_load_tested",
                      "ci_built_image"):
            if k73.get(field) is not False:
                errors.append(f"{path}: Run 21 {field} is overstated")
        if data.get("latest_authenticated_working_run") != 21:
            errors.append(f"{path}: latest authenticated working run must be 21")
        if data.get("latest_authenticated_working_run_scope") != (
                "numbered-regular-console-run-only"):
            errors.append(f"{path}: latest numbered-run scope is ambiguous")
        if data.get("latest_tested_run") != "ps5-pro-linux-test3-pass":
            errors.append(f"{path}: latest tested result must be PS5 Pro Test 3")

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
