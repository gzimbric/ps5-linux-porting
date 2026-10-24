import hashlib
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.check_ubuntu2404_usb import (
    FileIdentity,
    RUN16_BOOT_FILES,
    RUN16_ROOT_INITRD,
    verify_boot_directory,
    verify_initrd_relationship,
)
from tools.check_links import check as check_links
from tools.check_public_tree import check as check_public_tree
from tools.classify_1160_log import classify
from tools.validate_manifests import validate


ROOT = Path(__file__).resolve().parents[1]
TEST_SOURCE_COMMIT = "1" * 40
TEST_SOURCE_TREE = "2" * 40


def load_pinned_manifest() -> dict:
    data = json.loads((ROOT / "firmwares" / "11.60.json").read_text())
    image_builder = data["ubuntu_control"]["image_builder"]
    image_builder["pin_complete"] = True
    image_builder["published_commit"] = TEST_SOURCE_COMMIT
    image_builder["published_tree"] = TEST_SOURCE_TREE
    return data


def load_publishable_manifest() -> dict:
    data = load_pinned_manifest()
    image_builder = data["ubuntu_control"]["image_builder"]
    image_builder["clean_kernel_build_validated"] = True
    image_builder["full_clean_image_build_validated"] = True
    image_builder["one_command_reproduction_validated"] = False
    return data


class ToolTests(unittest.TestCase):
    def test_manifest(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_publishable_manifest()
            path.write_text(json.dumps(data))
            self.assertEqual(validate(path), [])
        bounded = data["bounded_loader_diagnostics"]
        self.assertEqual(
            bounded["source_commit"],
            "779af2f58aec61351278dd36cae9306e087ee873",
        )
        self.assertEqual(bounded["stage0"]["result"], "pass-responsive")
        self.assertEqual(bounded["stage1"]["leaf_ptes"], 10136)
        self.assertTrue(bounded["stage1"]["rollback_verified"])
        self.assertEqual(
            bounded["stage1b"]["sha256"],
            "57dc30301290702e935475816921f4a5ce0b5ab9a3097dafd75343988238d1e2",
        )
        self.assertTrue(bounded["stage1b"]["aliases_dereferenced"])
        self.assertFalse(bounded["stage1b"]["tlb_shootdown"])
        self.assertEqual(
            bounded["stage2a"]["sha256"],
            "38d913b5a484a89ae46f13c9fe1c078452e1c20adf6dd6b0091f45942ad15a8b",
        )
        self.assertTrue(bounded["stage2a"]["pid1_mapping"])
        self.assertTrue(bounded["stage2a"]["ui_responsive"])
        self.assertFalse(bounded["stage2a"]["executed"])
        self.assertTrue(data["linux_booted"])
        self.assertTrue(data["checkpoints"]["authenticated_linux_userspace"])
        pro = data["ps5_pro_linux_test3"]
        self.assertEqual(pro["console_count"], 1)
        self.assertEqual(pro["cold_boots_with_visible_hdmi"], 2)
        self.assertEqual(pro["display_resolution"], "1920x1080")
        self.assertTrue(pro["authenticated_wired_ssh"])
        self.assertTrue(pro["onboard_wifi_working"])
        self.assertTrue(pro["usb_input_working_with_autosuspend_disabled"])
        self.assertEqual(pro["loader_asset_name"],
                         "ps5-linux-loader-1160-dma-e820-bounded.elf")
        self.assertEqual(pro["loader_asset_size"], 189816)
        self.assertEqual(
            pro["loader_asset_sha256"],
            "3ab6609fb36edec23d3964215690563cb92071a0831f00608d977d9d7be7ce0b",
        )
        self.assertEqual(pro["image_asset_name"], "ps5-ubuntu2404-k73.img.xz")
        self.assertEqual(pro["image_asset_size"], 1726066320)
        self.assertEqual(
            pro["image_asset_sha256"],
            "9f038b316be5595b5b1629a86470cd7b955cf977741e022d9e1135898746de04",
        )
        self.assertFalse(pro["bluetooth_working"])
        self.assertFalse(pro["pro_frequency_control_tested"])
        self.assertFalse(pro["gpu_temperature_available"])
        self.assertFalse(pro["games_tested"])
        display = data["sonic_display_diagnostics"]
        self.assertEqual(
            display["last_tested_source_commit"],
            "815b1fdc5c76088762e42ad0ad80b0099a54e60d",
        )
        self.assertTrue(display["run12"]["authenticated_working_baseline"])
        self.assertEqual(display["run13"]["attempts"], 2)
        self.assertEqual(
            display["run13"]["elf_sha256"],
            "651462323382cf4c17f01786d6a57f8abe9e35afe6c4834a48ade582c115e3ce",
        )
        self.assertTrue(display["run14"]["initializer_only_control"])
        self.assertTrue(display["run14"]["mp3_initialize_validated"])
        self.assertFalse(display["run14"]["runtime_clear_executed"])
        self.assertEqual(
            display["run14"]["elf_sha256"],
            "7da712a578fcf83798db46f6f5295224e7ccf345d0f7eb7fb7c3e73564d325d4",
        )
        self.assertFalse(display["production_runtime_clear_required"])
        run15 = display["run15"]
        self.assertTrue(run15["release_loader_baseline"])
        self.assertTrue(run15["visible_display_observed"])
        self.assertFalse(run15["runtime_clear_executed"])
        self.assertEqual(run15["display_table_operations"], 29)
        self.assertEqual(
            run15["elf_sha256"],
            "422b87ec39ca0edfce8dddd609c2eff1cc7adcb2732b7909b76fafbd60dd2336",
        )
        self.assertEqual(display["release"]["elf_sha256"], run15["elf_sha256"])
        self.assertEqual(
            display["release"]["published_source"]["release_check_commit"],
            "69657e6127db2ff9cc9ac2ad5e5aaebaa8019daf",
        )
        self.assertTrue(
            display["release"]["published_source"][
                "release_check_reproduces_run15_artifacts"
            ]
        )
        ubuntu = data["ubuntu_control"]
        self.assertEqual(data["latest_authenticated_working_run"], 21)
        self.assertEqual(ubuntu["run"], 16)
        self.assertTrue(ubuntu["loader"]["byte_identical_to_run15"])
        self.assertFalse(ubuntu["initrd"]["byte_identical_to_run15"])
        self.assertEqual(ubuntu["initrd"]["zero_padding_bytes"], 3573156)
        image_builder = ubuntu["image_builder"]
        self.assertTrue(image_builder["customized_from_upstream"])
        self.assertEqual(
            image_builder["kernel_input_source"],
            "separate-deterministic-run15-baseline-build",
        )
        self.assertTrue(image_builder["fixed_kbuild_user_and_host"])
        self.assertTrue(image_builder["date_shim_used"])
        self.assertTrue(image_builder["deterministic_kernel_recipe_integrated"])
        self.assertTrue(image_builder["kernel_package_reused"])
        self.assertTrue(image_builder["clean_kernel_build_validated"])
        self.assertTrue(image_builder["full_clean_image_build_validated"])
        self.assertFalse(image_builder["one_command_reproduction_validated"])
        self.assertTrue(image_builder["pin_complete"])
        self.assertEqual(
            image_builder["published_commit"],
            TEST_SOURCE_COMMIT,
        )
        self.assertEqual(
            image_builder["published_tree"],
            TEST_SOURCE_TREE,
        )
        self.assertEqual(ubuntu["partitions"]["logical_sector_size"], 512)
        self.assertEqual(ubuntu["partitions"]["root"]["label"], "ubuntu2404")
        self.assertEqual(
            ubuntu["partitions"]["root"],
            {
                "number": 1,
                "filesystem": "ext4",
                "label": "ubuntu2404",
                "start_sector": 1024000,
                "end_sector": 32765951,
                "size_sectors": 31741952,
            },
        )
        self.assertEqual(ubuntu["partitions"]["efi"]["label"], "boot")
        self.assertEqual(
            ubuntu["partitions"]["efi"],
            {
                "number": 2,
                "filesystem": "fat32",
                "label": "boot",
                "start_sector": 2048,
                "end_sector": 1023999,
                "size_sectors": 1021952,
            },
        )
        self.assertFalse(ubuntu["disk_image"]["included"])
        for filename, manifest_name in {
            "bzImage": "kernel",
            "initrd.img": "initrd",
            "cmdline.txt": "cmdline",
            "vram.txt": "vram",
            "kexec.sh": "kexec",
        }.items():
            self.assertEqual(
                RUN16_BOOT_FILES[filename].size,
                ubuntu[manifest_name]["size"],
            )
            self.assertEqual(
                RUN16_BOOT_FILES[filename].sha256,
                ubuntu[manifest_name]["sha256"],
            )
        self.assertEqual(
            RUN16_ROOT_INITRD.size,
            ubuntu["initramfs_unpadded"]["size"],
        )
        self.assertEqual(
            RUN16_ROOT_INITRD.sha256,
            ubuntu["initramfs_unpadded"]["sha256"],
        )
        self.assertFalse(ubuntu["wireless"]["mt7921_applicable"])
        self.assertTrue(data["checkpoints"]["visible_hdmi"])
        self.assertTrue(
            data["checkpoints"]["mp3_commands_21_22_present_in_successful_path"]
        )
        self.assertTrue(
            data["checkpoints"]["display_operation_table_present_in_successful_path"]
        )
        self.assertFalse(
            data["checkpoints"]["individual_mp3_and_table_returns_observed"]
        )
        self.assertTrue(data["boot_media"]["physical_usb_boot_partition_verified"])
        self.assertEqual(data["boot_media"]["run"], 15)
        self.assertEqual(data["boot_media"]["distribution"], "CachyOS")
        self.assertEqual(
            data["boot_media"]["initrd"]["sha256"],
            "c37b88569ef8f05b0b4ae432a8ec0fd323b7a3537a6441f8c45baaad45ff061f",
        )

    def test_links(self):
        self.assertEqual(check_links(ROOT), [])

    def test_public_tree(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "README.md").write_text("Complete public tree.\n")
            self.assertEqual(check_public_tree(root), [])

    def test_run15_amdgpu_config(self):
        path = ROOT / "config" / "ps5-amdgpu.conf"
        self.assertEqual(
            hashlib.sha256(path.read_bytes()).hexdigest(),
            "51dbae6f372fa1f5bceee2fd95403042bb6954d29b3f9db2a11c769dd41fc677",
        )
        self.assertEqual(path.stat().st_size, 195)

    def test_ubuntu_boot_file_verifier(self):
        with TemporaryDirectory() as temp:
            efi = Path(temp) / "efi"
            efi.mkdir()
            contents = {
                "bzImage": b"kernel",
                "initrd.img": b"initrd",
                "cmdline.txt": b"root=test\n",
                "vram.txt": b"vram\n",
                "kexec.sh": b"script\n",
            }
            expected = {}
            for name, content in contents.items():
                (efi / name).write_bytes(content)
                expected[name] = FileIdentity(
                    len(content), hashlib.sha256(content).hexdigest()
                )

            self.assertEqual(verify_boot_directory(efi, expected), [])
            (efi / "cmdline.txt").write_bytes(b"root=wrong\n")
            errors = verify_boot_directory(efi, expected)
            self.assertTrue(any("cmdline.txt" in error for error in errors))

    def test_ubuntu_initrd_padding_verifier(self):
        with TemporaryDirectory() as temp:
            root_initrd = Path(temp) / "initrd.img-7.1.7"
            efi_initrd = Path(temp) / "initrd.img"
            root_content = b"root-initramfs"
            efi_content = root_content + b"\0" * 7
            root_initrd.write_bytes(root_content)
            efi_initrd.write_bytes(efi_content)
            expected_root = FileIdentity(
                len(root_content), hashlib.sha256(root_content).hexdigest()
            )
            expected_efi = FileIdentity(
                len(efi_content), hashlib.sha256(efi_content).hexdigest()
            )

            self.assertEqual(
                verify_initrd_relationship(
                    root_initrd, efi_initrd, expected_root, expected_efi
                ),
                [],
            )
            nonzero_tail = root_content + b"\0" * 6 + b"x"
            efi_initrd.write_bytes(nonzero_tail)
            expected_nonzero = FileIdentity(
                len(nonzero_tail), hashlib.sha256(nonzero_tail).hexdigest()
            )
            errors = verify_initrd_relationship(
                root_initrd, efi_initrd, expected_root, expected_nonzero
            )
            self.assertTrue(any("nonzero data" in error for error in errors))

    def test_classifier(self):
        text = "\n".join([
            "Welcome to pLinux5-NG",
            "strike chain=0 done=0 err=0 self=1 tgt=16 wr=16 ver=16",
            "11.60: existing bypass verified; beginning Linux handoff.",
            "11.60: live HV VMMCALL handler validated at PA 0x62847551.",
            "11.60 preflight: Linux images staged successfully.",
        ])
        result = classify(text)
        self.assertEqual(result["last_checkpoint"], "images-staged")
        self.assertTrue(result["validated_bypass_shape_present"])
        self.assertFalse(result["linux_boot_observed"])

    def test_classifier_official_stage1(self):
        text = "\n".join([
            "11.60 stage 1: regular-console diagnostic starting",
            "11.60 stage 1: source preflight passed (2534 logical 16 KiB pages)",
            "11.60 stage 1: target range preflight passed",
            "11.60 stage 1: all alias PTEs verified",
            "11.60 stage 1: rollback verified (10136 PTEs, 10158 writes, 22 temporary table pages)",
            "11.60 STAGE 1 PASS; no HV, hook, rest-mode, or wake code linked",
        ])
        result = classify(text)
        self.assertEqual(result["last_checkpoint"], "official-stage1-pass")
        self.assertFalse(result["linux_boot_observed"])

    def test_classifier_official_stage0(self):
        text = "\n".join([
            "11.60 stage 0: regular-console diagnostic starting",
            "11.60 stage 0: read-only boundary complete; no page-table writes attempted",
            "11.60 STAGE 0 PASS; no HV, hook, rest-mode, or wake code linked",
        ])
        result = classify(text)
        self.assertEqual(result["last_checkpoint"], "official-stage0-pass")
        self.assertFalse(result["linux_boot_observed"])

    def test_classifier_official_stage1b(self):
        text = "\n".join([
            "11.60 stage 1B: regular-console data read-through diagnostic starting",
            "11.60 stage 1B: preflight passed for one 16 KiB data canary",
            "11.60 stage 1B: shared subtree linked into current pmap",
            "11.60 stage 1B: full 16 KiB canary matched through target virtual address",
            "11.60 stage 1B: hardware Accessed bits observed on all four leaf PTEs",
            "11.60 stage 1B: both pmap roots restored and verified absent",
            "11.60 STAGE 1B PASS; data alias read-through verified; page tables rolled back",
            "11.60 stage 1B: PASS containment active; backing retained and cold reboot required",
        ])
        result = classify(text)
        self.assertEqual(result["last_checkpoint"], "official-stage1b-hold")
        self.assertFalse(result["linux_boot_observed"])

    def test_classifier_official_stage2a(self):
        text = "\n".join([
            "11.60 Stage 2A: staging the inert official wake page only.",
            "11.60 Stage 2A PASS: inert wake page staged RX at fixed alias; no hook/HV/rest/Linux action was taken",
            "11.60 Stage 2A is holding the verified backing page. GameOS should remain responsive. Cold reboot after recording the result.",
        ])
        result = classify(text)
        self.assertEqual(result["last_checkpoint"], "official-stage2a-hold")
        self.assertFalse(result["linux_boot_observed"])

    def test_classifier_run15_sender_capture(self):
        text = "\n".join([
            "11.60 checkpoint: main: fetch_linux call",
            "11.60 loader checkpoint: bzImage read complete (12702720 bytes)",
            "11.60 loader checkpoint: initrd read complete (54376639 bytes)",
            "11.60 alias staging: building checked source plan",
            "11.60 alias staging: source preflight passed (4096 logical 16-KiB pages)",
            "11.60 alias staging: target range preflight passed",
            "11.60 alias staging: installing checked aliases",
            "11.60 alias staging: all aliases installed",
            "11.60 alias staging: verifying alias PTEs",
            "11.60 alias staging: all 16384 leaf PTEs verified",
            "11.60 alias staging: PASS; source, info, and page-table backing retained",
            "11.60 checkpoint: main: fetch_linux returned 0",
            "11.60 checkpoint: main: prepare_resume call",
            "11.60 checkpoint: prepare_resume: argument preflight passed",
            "11.60 checkpoint: prepare_resume: argument readback passed",
            "11.60 checkpoint: prepare_resume: wake user mapping populated",
            "11.60 checkpoint: prepare_resume: wake alias install complete",
            "11.60 checkpoint: prepare_resume: remove_xotext complete",
            "11.60 checkpoint: prepare_resume: pmap invalidation complete",
            "11.60 checkpoint: main: prepare_resume returned 0",
            "11.60 checkpoint: main: hv_defeat_1160 call",
            "11.60 checkpoint: hv_defeat: offsets/raw firmware gate passed",
            "11.60 checkpoint: hv_defeat: regular-model gate passed",
            "11.60 checkpoint: hv_defeat: page-table-only wake-cave validation passed",
            "11.60 checkpoint: hv_defeat: runtime preflight passed",
            "11.60 checkpoint: hv_defeat: startup carrier arm complete",
            "11.60 checkpoint: hv_defeat: final IST7/IDT/FACS mutations complete",
            "11.60 Sonic-style Linux wake chain armed",
            "11.60 checkpoint: main: hv_defeat_1160 returned 0",
        ])
        result = classify(text)
        self.assertEqual(result["last_checkpoint"], "hv-defeat-return")
        self.assertFalse(result["linux_boot_observed"])
        self.assertFalse(result["refusal_observed"])
        self.assertFalse(result["cold_reboot_required"])

    def test_classifier_refusal(self):
        result = classify("11.60 loader REFUSED initrd size\nCold reboot required")
        self.assertEqual(result["last_checkpoint"], "cold-reboot-required")
        self.assertTrue(result["refusal_observed"])
        self.assertTrue(result["cold_reboot_required"])

    def test_public_tree_rejects_binary(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "payload.elf").write_bytes(b"x")
            self.assertTrue(check_public_tree(root))

    def test_public_tree_rejects_unfinished_source_pin(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            marker = "PENDING" + "-TESTED-SOURCE-COMMIT"
            (root / "README.md").write_text(marker)
            self.assertTrue(any(
                "unfinished tested-source pin" in error
                for error in check_public_tree(root)
            ))

    def test_public_tree_rejects_runtime_identifiers(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            machine_uuid = "-".join((
                "585b1bce", "aa09", "4310", "8cbf", "396b9523cc47",
            ))
            mac_address = ":".join(("aa", "bb", "cc", "dd", "ee", "ff"))
            (root / "evidence.md").write_text(
                f"boot={machine_uuid}\nmac={mac_address}\n"
            )
            errors = check_public_tree(root)
            self.assertTrue(any("machine UUID" in error for error in errors))
            self.assertTrue(any("machine MAC address" in error for error in errors))

    def test_public_tree_rejects_forbidden_attribution(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            assistant_name = "Cl" + "aude"
            (root / "README.md").write_text(
                f"Co-authored-by: {assistant_name}\n"
            )
            self.assertTrue(any(
                "forbidden attribution marker" in error
                for error in check_public_tree(root)
            ))

    def test_public_tree_allows_upstream_credit(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "README.md").write_text(
                "The 7.3 port and frequency drivers are by rmux, "
                "https://github.com/rmuxnet/ps5-linux-patches-1.\n"
            )
            self.assertEqual(check_public_tree(root), [])

    def test_manifest_requires_complete_ubuntu_source_pin(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_pinned_manifest()
            image_builder = data["ubuntu_control"]["image_builder"]
            image_builder["pin_complete"] = False
            path.write_text(json.dumps(data))
            self.assertTrue(any(
                "tested source pin must be complete" in error
                for error in validate(path)
            ))

    def test_manifest_requires_ubuntu_source_commit_and_tree(self):
        for field in ("published_commit", "published_tree"):
            with self.subTest(field=field), TemporaryDirectory() as temp:
                path = Path(temp) / "manifest.json"
                data = load_pinned_manifest()
                data["ubuntu_control"]["image_builder"][field] = "not-a-git-object"
                path.write_text(json.dumps(data))
                self.assertTrue(any(
                    f"invalid published Ubuntu source {field.removeprefix('published_')}"
                    in error
                    for error in validate(path)
                ))

    def test_manifest_requires_kernel_package_reuse_record(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_pinned_manifest()
            data["ubuntu_control"]["image_builder"]["kernel_package_reused"] = False
            path.write_text(json.dumps(data))
            self.assertTrue(any(
                "must record kernel package reuse" in error
                for error in validate(path)
            ))

    def test_manifest_rejects_ubuntu_partition_geometry_drift(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_pinned_manifest()
            data["ubuntu_control"]["partitions"]["root"]["end_sector"] -= 1
            path.write_text(json.dumps(data))
            self.assertTrue(any(
                "unexpected Ubuntu partition layout" in error
                for error in validate(path)
            ))

    def test_manifest_rejects_invalid_candidate_digest(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_pinned_manifest()
            data["superseded_candidate_build"]["sha256"]["final_elf"] = "not-a-digest"
            path.write_text(json.dumps(data))
            self.assertTrue(any("candidate SHA-256" in error
                                for error in validate(path)))

    def test_manifest_requires_bounded_diagnostics(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_pinned_manifest()
            del data["bounded_loader_diagnostics"]
            path.write_text(json.dumps(data))
            self.assertTrue(any("bounded_loader_diagnostics" in error
                                for error in validate(path)))

    def test_manifest_rejects_invalid_bounded_stage_hash(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_pinned_manifest()
            data["bounded_loader_diagnostics"]["stage1"]["sha256"] = "bad"
            path.write_text(json.dumps(data))
            self.assertTrue(any("bounded stage1 SHA-256" in error
                                for error in validate(path)))

    def test_manifest_rejects_bounded_count_drift(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_pinned_manifest()
            data["bounded_loader_diagnostics"]["stage1"]["leaf_ptes"] -= 1
            path.write_text(json.dumps(data))
            self.assertTrue(any("inconsistent bounded stage1 counts" in error
                                for error in validate(path)))

    def test_manifest_rejects_false_alias_readthrough(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_pinned_manifest()
            data["checkpoints"]["syscore_alias_read_through"] = False
            path.write_text(json.dumps(data))
            self.assertTrue(any("syscore read-through disagrees" in error
                                for error in validate(path)))

    def test_manifest_rejects_executed_stage2a(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_pinned_manifest()
            data["bounded_loader_diagnostics"]["stage2a"]["executed"] = True
            path.write_text(json.dumps(data))
            self.assertTrue(any("stage2a requires executed=false" in error
                                for error in validate(path)))

    def test_manifest_rejects_overstated_display_telemetry(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_pinned_manifest()
            data["checkpoints"]["individual_mp3_and_table_returns_observed"] = True
            path.write_text(json.dumps(data))
            self.assertTrue(any("return scope is overstated" in error
                                for error in validate(path)))

    def test_manifest_rejects_invalid_published_source_commit(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_pinned_manifest()
            release = data["sonic_display_diagnostics"]["release"]
            release["published_source"]["commit"] = "bad"
            path.write_text(json.dumps(data))
            self.assertTrue(any("invalid published source commit" in error
                                for error in validate(path)))

    def test_manifest_rejects_ubuntu_initrd_drift(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_pinned_manifest()
            data["ubuntu_control"]["initrd"]["sha256"] = "0" * 64
            path.write_text(json.dumps(data))
            self.assertTrue(any("Ubuntu control initrd SHA-256" in error
                                for error in validate(path)))

    def test_manifest_rejects_ubuntu_source_base_drift(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_pinned_manifest()
            data["ubuntu_control"]["image_builder"]["upstream_base_commit"] = "0" * 40
            path.write_text(json.dumps(data))
            self.assertTrue(any("image builder upstream_base_commit" in error
                                for error in validate(path)))

    def test_manifest_rejects_ubuntu_initrd_padding_drift(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_pinned_manifest()
            data["ubuntu_control"]["initrd"]["zero_padding_bytes"] = 1
            path.write_text(json.dumps(data))
            errors = validate(path)
            self.assertTrue(any("Ubuntu initrd padding" in error
                                for error in errors))
            self.assertTrue(any("padding arithmetic" in error
                                for error in errors))

    def test_manifest_rejects_latest_run_drift(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_pinned_manifest()
            data["latest_authenticated_working_run"] = 19
            path.write_text(json.dumps(data))
            self.assertTrue(any("latest authenticated working run" in error
                                for error in validate(path)))

    def test_manifest_records_run17_wifi(self):
        data = load_pinned_manifest()
        wifi = data["ubuntu_wifi"]
        self.assertEqual(wifi["run"], 17)
        self.assertEqual(wifi["firmware"]["size"], 0x799BC)
        self.assertNotIn("ps5-iw620-kernel72-compat.patch",
                         wifi["driver"]["patches"])
        self.assertFalse(wifi["autoload_observed_across_reboot"])

    def test_manifest_rejects_kernel72_patch_on_717(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_pinned_manifest()
            data["ubuntu_wifi"]["driver"]["kernel72_compat_applied"] = True
            path.write_text(json.dumps(data))
            self.assertTrue(any("7.2 compatibility patch" in error
                                for error in validate(path)))

    def test_manifest_rejects_wifi_built_without_objtool(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_pinned_manifest()
            data["ubuntu_wifi"]["driver"]["objtool_disabled"] = True
            path.write_text(json.dumps(data))
            self.assertTrue(any("built with objtool" in error
                                for error in validate(path)))

    def test_manifest_rejects_wifi_module_drift(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_pinned_manifest()
            data["ubuntu_wifi"]["modules"]["moal"]["sha256"] = "0" * 64
            path.write_text(json.dumps(data))
            self.assertTrue(any("Wi-Fi module moal SHA-256" in error
                                for error in validate(path)))

    def test_manifest_rejects_included_wifi_firmware(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_pinned_manifest()
            data["ubuntu_wifi"]["firmware"]["included"] = True
            path.write_text(json.dumps(data))
            self.assertTrue(any("firmware must not be included" in error
                                for error in validate(path)))

    def test_manifest_rejects_wifi_firmware_size_drift(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_pinned_manifest()
            data["ubuntu_wifi"]["firmware"]["size_hex"] = "not-hex"
            path.write_text(json.dumps(data))
            errors = validate(path)
            self.assertTrue(any("firmware size_hex" in error for error in errors))
            self.assertTrue(any("inconsistent Ubuntu Wi-Fi firmware size" in error
                                for error in errors))

    def test_manifest_rejects_overstated_wifi_scope(self):
        for field in ("autoload_observed_across_reboot", "soak_tested",
                      "driver_reload_tested"):
            with self.subTest(field=field), TemporaryDirectory() as temp:
                path = Path(temp) / "manifest.json"
                data = load_pinned_manifest()
                data["ubuntu_wifi"][field] = True
                path.write_text(json.dumps(data))
                self.assertTrue(any(f"{field} is overstated" in error
                                    for error in validate(path)))

    def test_manifest_rejects_untested_loader_dump_claim(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_pinned_manifest()
            data["ubuntu_wifi"]["firmware"]["loader_dump_hardware_tested"] = True
            path.write_text(json.dumps(data))
            self.assertTrue(any("loader firmware dump has not run on hardware" in error
                                for error in validate(path)))

    def test_manifest_records_run18_dma_e820(self):
        data = load_pinned_manifest()
        dma = data["dma_e820_build"]
        self.assertEqual(dma["run"], 18)
        self.assertEqual(
            dma["loader"]["sha256"],
            "2e1758a2d013305bcb9faa0eb3adf18c34ed76ad85313dd945719c8bf2a0c9c0",
        )
        self.assertFalse(dma["loader"]["byte_identical_to_run15"])
        self.assertTrue(dma["loader"]["output_byte_identical_to_run16"])
        self.assertEqual(dma["observed_e820"]["reserved"]["start"],
                         "0x0000000001000000")
        self.assertEqual(dma["observed_e820"]["reserved"]["end_inclusive"],
                         "0x000000003fffffff")
        self.assertEqual(dma["io_check"]["bytes_written"], 12 * 2**30)
        self.assertFalse(dma["release_loader_baseline"])
        self.assertTrue(
            data["sonic_display_diagnostics"]["run15"]["release_loader_baseline"])
        self.assertEqual(data["boot_media"]["run"], 15)

    def test_manifest_rejects_dma_loader_hash_drift(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_pinned_manifest()
            data["dma_e820_build"]["loader"]["sha256"] = (
                "422b87ec39ca0edfce8dddd609c2eff1cc7adcb2732b7909b76fafbd60dd2336"
            )
            path.write_text(json.dumps(data))
            errors = validate(path)
            self.assertTrue(any("Run 18 DMA loader SHA-256" in error
                                for error in errors))
            self.assertTrue(any("Run 15 must remain the release loader ELF" in error
                                for error in errors))

    def test_manifest_rejects_dma_build_as_release_baseline(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_pinned_manifest()
            data["dma_e820_build"]["release_loader_baseline"] = True
            path.write_text(json.dumps(data))
            self.assertTrue(any("must not replace the Run 15 release baseline" in error
                                for error in validate(path)))

    def test_manifest_rejects_overstated_dma_scope(self):
        for field in ("independent_hardware_reproduction", "ab_control_run",
                      "tester_errors_reproduced", "soak_tested",
                      "physical_display_observed", "ubuntu_ci_image_tested"):
            with self.subTest(field=field), TemporaryDirectory() as temp:
                path = Path(temp) / "manifest.json"
                data = load_pinned_manifest()
                data["dma_e820_build"][field] = True
                path.write_text(json.dumps(data))
                self.assertTrue(any(f"Run 18 {field} is overstated" in error
                                    for error in validate(path)))

    def test_manifest_rejects_wrong_dma_reserved_range(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_pinned_manifest()
            data["dma_e820_build"]["observed_e820"]["reserved"]["start"] = (
                "0x000000003fffc000"
            )
            path.write_text(json.dumps(data))
            self.assertTrue(any("Run 18 observed e820 reserved range" in error
                                for error in validate(path)))

    def test_manifest_rejects_dma_loader_map_drift(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_pinned_manifest()
            data["dma_e820_build"]["loader"]["reserved"]["start"] = "0x3fffc000"
            path.write_text(json.dumps(data))
            errors = validate(path)
            self.assertTrue(any("Run 18 DMA loader reserved range" in error
                                for error in errors))
            self.assertTrue(any("disagrees with the loader map" in error
                                for error in errors))

    def test_manifest_rejects_inconsistent_dma_io_check(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_pinned_manifest()
            data["dma_e820_build"]["io_check"]["bytes_written"] = 2**30
            path.write_text(json.dumps(data))
            self.assertTrue(any("inconsistent Run 18 I/O check size" in error
                                for error in validate(path)))

    def test_manifest_records_run19_ubuntu_ci_dma(self):
        data = load_pinned_manifest()
        run19 = data["ubuntu_ci_dma_run"]
        self.assertEqual(run19["run"], 19)
        self.assertEqual(run19["image"]["release_tag"], "ubuntu2404-1160-build-3")
        self.assertEqual(
            run19["image"]["raw"]["sha256"],
            "cb01a4f53dedc390a07cdcd42b93dda0762e0c4dee8efe0130af7bdb36ba7fda",
        )
        self.assertEqual(run19["loader"]["sha256"],
                         data["dma_e820_build"]["loader"]["sha256"])
        self.assertTrue(run19["loader"]["output_byte_identical_to_run18"])
        self.assertEqual(run19["boot_files"]["initrd"]["size"], 54376639)
        self.assertNotEqual(run19["boot_files"]["initrd"]["sha256"],
                            data["ubuntu_control"]["initrd"]["sha256"])
        self.assertEqual(run19["observed_e820"]["reserved"],
                         data["dma_e820_build"]["observed_e820"]["reserved"])
        self.assertEqual(run19["mem_total_kib"],
                         data["dma_e820_build"]["mem_total_kib"])
        self.assertEqual(
            run19["tester_guide_checks"]["io_check"]["bytes_written"], 12 * 2**30)
        self.assertTrue(run19["physical_display_observed"])
        self.assertTrue(run19["display"]["direct_operator_observation"])
        self.assertEqual(run19["wake"]["attempts"], 1)
        self.assertEqual(len(run19["image_defects"]), 2)
        self.assertFalse(run19["release_loader_baseline"])
        self.assertTrue(
            data["sonic_display_diagnostics"]["run15"]["release_loader_baseline"])
        self.assertEqual(data["dma_e820_build"]["run"], 18)
        self.assertTrue(run19["published_tester_pair"])

    def test_manifest_requires_run19_record(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_pinned_manifest()
            del data["ubuntu_ci_dma_run"]
            path.write_text(json.dumps(data))
            errors = validate(path)
            self.assertTrue(any("missing ubuntu_ci_dma_run" in error
                                for error in errors))
            self.assertTrue(any("ubuntu_ci_dma_run is not an object" in error
                                for error in errors))

    def test_manifest_rejects_run19_loader_hash_drift(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_pinned_manifest()
            data["ubuntu_ci_dma_run"]["loader"]["sha256"] = (
                "422b87ec39ca0edfce8dddd609c2eff1cc7adcb2732b7909b76fafbd60dd2336"
            )
            path.write_text(json.dumps(data))
            errors = validate(path)
            self.assertTrue(any("Run 19 loader SHA-256" in error
                                for error in errors))
            self.assertTrue(any("Run 19 loader must be the Run 18 DMA loader" in error
                                for error in errors))
            self.assertTrue(any("Run 15 must remain the release loader ELF" in error
                                for error in errors))

    def test_manifest_rejects_run19_image_hash_drift(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_pinned_manifest()
            data["ubuntu_ci_dma_run"]["image"]["raw"]["sha256"] = (
                "bf4bca3ab6583c74eb06b17e8c3e4243972690a38fa40bd9a652c6d71a7ee347"
            )
            path.write_text(json.dumps(data))
            self.assertTrue(any("unexpected Run 19 image SHA-256" in error
                                for error in validate(path)))

    def test_manifest_rejects_run19_boot_file_drift(self):
        cases = (
            ("initrd", "size", 54376640, "Run 19 boot file initrd size"),
            ("bzimage", "sha256", "0" * 64, "Run 19 boot file bzimage SHA-256"),
        )
        for name, field, value, message in cases:
            with self.subTest(name=name), TemporaryDirectory() as temp:
                path = Path(temp) / "manifest.json"
                data = load_pinned_manifest()
                data["ubuntu_ci_dma_run"]["boot_files"][name][field] = value
                path.write_text(json.dumps(data))
                self.assertTrue(any(message in error for error in validate(path)))

    def test_manifest_rejects_wrong_run19_reserved_range(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_pinned_manifest()
            data["ubuntu_ci_dma_run"]["observed_e820"]["reserved"]["start"] = (
                "0x000000003fffc000"
            )
            path.write_text(json.dumps(data))
            self.assertTrue(any("Run 19 observed e820 reserved range" in error
                                for error in validate(path)))

    def test_manifest_requires_run19_display_observation(self):
        for target in ("run", "display"):
            with self.subTest(target=target), TemporaryDirectory() as temp:
                path = Path(temp) / "manifest.json"
                data = load_pinned_manifest()
                run19 = data["ubuntu_ci_dma_run"]
                if target == "run":
                    run19["physical_display_observed"] = False
                else:
                    run19["display"]["direct_operator_observation"] = False
                path.write_text(json.dumps(data))
                self.assertTrue(any("Run 19 must record the directly observed display"
                                    in error for error in validate(path)))

    def test_manifest_rejects_overstated_run19_scope(self):
        for field in ("independent_hardware_reproduction", "ab_control_run",
                      "tester_errors_reproduced", "soak_tested", "wifi_tested"):
            with self.subTest(field=field), TemporaryDirectory() as temp:
                path = Path(temp) / "manifest.json"
                data = load_pinned_manifest()
                data["ubuntu_ci_dma_run"][field] = True
                path.write_text(json.dumps(data))
                self.assertTrue(any(f"Run 19 {field} is overstated" in error
                                    for error in validate(path)))

    def test_manifest_rejects_inconsistent_run19_io_check(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_pinned_manifest()
            data["ubuntu_ci_dma_run"]["tester_guide_checks"]["io_check"][
                "bytes_written"] = 2**30
            path.write_text(json.dumps(data))
            self.assertTrue(any("inconsistent Run 19 I/O check size" in error
                                for error in validate(path)))

    def test_manifest_rejects_latest_tested_run_drift(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_pinned_manifest()
            data["latest_tested_run"] = "run19-ubuntu-ci-dma-e820-pass"
            path.write_text(json.dumps(data))
            self.assertTrue(any("latest tested result must be PS5 Pro Test 3" in error
                                for error in validate(path)))

    def test_manifest_rejects_overstated_ps5_pro_test3_scope(self):
        for field in ("bluetooth_working", "pro_frequency_control_tested",
                      "gpu_temperature_available", "games_tested",
                      "boot_report_service_passed",
                      "regular_console_hardware_tested_with_this_image"):
            with self.subTest(field=field), TemporaryDirectory() as temp:
                path = Path(temp) / "manifest.json"
                data = load_pinned_manifest()
                data["ps5_pro_linux_test3"][field] = True
                path.write_text(json.dumps(data))
                self.assertTrue(any(
                    f"unexpected PS5 Pro Test 3 {field}" in error
                    for error in validate(path)
                ))

    def test_manifest_rejects_ps5_pro_test3_artifact_identity_drift(self):
        for field, value in (
                ("loader_asset_size", 189815),
                ("loader_asset_sha256", "0" * 64),
                ("image_asset_size", 1726066319),
                ("image_asset_sha256", "0" * 64)):
            with self.subTest(field=field), TemporaryDirectory() as temp:
                path = Path(temp) / "manifest.json"
                data = load_pinned_manifest()
                data["ps5_pro_linux_test3"][field] = value
                path.write_text(json.dumps(data))
                self.assertTrue(any(
                    f"unexpected PS5 Pro Test 3 {field}" in error
                    for error in validate(path)
                ))

    def test_manifest_records_run21_cachyos_k73(self):
        data = load_pinned_manifest()
        run21 = data["cachyos_k73_run"]
        self.assertEqual(run21["run"], 21)
        self.assertEqual(run21["kernel"]["version"], "7.3.0")
        self.assertEqual(run21["upstream_kernel_work"]["author"], "rmux")
        self.assertEqual(run21["upstream_kernel_work"]["repository"],
                         "https://github.com/rmuxnet/ps5-linux-patches-1")
        self.assertTrue(run21["kernel"]["patch_commit"].startswith("36f173f"))
        self.assertFalse(run21["image"]["built_by_ci"])
        self.assertEqual(run21["later_ci_build"]["workflow_conclusion"], "success")
        self.assertTrue(run21["later_ci_build"]["draft_release_created"])
        self.assertFalse(run21["later_ci_build"]["booted"])
        self.assertEqual(run21["later_ci_build"]["superseded_by"],
                         "cachyos1160-k73-image-2")
        image2 = run21["ci_build_2"]
        self.assertEqual(image2["release_tag"], "cachyos1160-k73-image-2")
        self.assertEqual(
            image2["source_commit"],
            "346088a48f66eb956dafdec9de5085e73b2d44a5",
        )
        self.assertEqual(image2["workflow_run"], 39481460775)
        self.assertEqual(image2["workflow_conclusion"], "success")
        self.assertTrue(image2["ci_result_verified"])
        self.assertEqual(
            image2["release_url"],
            "https://github.com/gzimbric/ps5-linux-image/releases/tag/cachyos1160-k73-image-2",
        )
        self.assertEqual(
            image2["release_policy"],
            "public-prerelease-for-hardware-testing",
        )
        self.assertTrue(image2["draft_release_created"])
        self.assertFalse(image2["release_is_draft"])
        self.assertTrue(image2["release_is_prerelease"])
        self.assertTrue(image2["published_for_testing"])
        self.assertFalse(image2["booted"])
        self.assertEqual(image2["kernel_package"]["version"], "7.3.0-2")
        self.assertTrue(image2["base_patch_set"]["used_as_published"])
        self.assertFalse(
            image2["bluetooth_followup_patch"]["hardware_tested"])
        self.assertEqual(image2["fan_policy"]["servo_pattern"], 3)
        self.assertTrue(image2["fan_policy"]["enabled_by_default"])
        self.assertFalse(image2["fan_policy"]["dynamic_temperature_curve"])
        external_bt = image2["bluetooth_followup_patch"]["external_confirmation"]
        self.assertEqual(external_bt["release_tag"], "v1.0.3")
        self.assertEqual(
            external_bt["patch_sha256"],
            "c01bdcc134f25a86825f2824d12a82da02db18e7b1940db722223b0c4611eed8",
        )
        self.assertEqual(external_bt["firmware"], "13.60")
        self.assertTrue(external_bt["same_core_fix"])
        self.assertFalse(external_bt["byte_identical_patch"])
        self.assertFalse(external_bt["image2_hardware_test"])
        self.assertEqual(
            image2["release_asset_policy"]["format"], "single-img-xz")
        self.assertTrue(
            image2["release_asset_policy"]["fail_instead_of_split"])
        asset = image2["release_asset_policy"]
        self.assertTrue(asset["verified"])
        self.assertEqual(asset["asset_name"], "ps5-cachyos1160-k73.img.xz")
        self.assertEqual(asset["size"], 1943471712)
        self.assertEqual(
            asset["sha256"],
            "8b785243f79a32a4155cc1e39bed01d580e25ca514e88abbfed1a8a8157a281a",
        )
        raw_image = image2["raw_image"]
        self.assertTrue(raw_image["verified"])
        self.assertEqual(raw_image["name"], "ps5-cachyos1160-k73.img")
        self.assertEqual(raw_image["size"], 12582912000)
        self.assertEqual(
            raw_image["sha256"],
            "3798c7dba96412c5301eb201d8bf8aa4edd1b2f80a743dfd7b90b2a79222c62d",
        )
        self.assertEqual(
            run21["image"]["raw"]["sha256"],
            "d593bb5d52c9054d8e3671d6b67fae0687aa239cb3d104a503999e6a5906789d",
        )
        self.assertEqual(
            run21["loader"]["sha256"],
            "e9fe6469943e97a635eccd3f674e55876b56cd1bbd69023eee3af4acea3a1b5f",
        )
        loader = run21["loader"]
        self.assertEqual(
            loader["release_url"],
            "https://github.com/gzimbric/ps5-linux-loader/releases/tag/firmware-11.60-dma-e820-bounded-run21",
        )
        self.assertFalse(loader["release_is_draft"])
        self.assertTrue(loader["release_is_prerelease"])
        self.assertTrue(loader["published_for_testing"])
        self.assertTrue(loader["release_assets"]["bounded_wifi"]["hardware_booted"])
        self.assertFalse(
            loader["release_assets"]["bounded_wifi"][
                "booted_with_exact_ci_image_2"
            ]
        )
        self.assertFalse(
            loader["release_assets"]["bounded_non_wifi"]["hardware_booted"])
        self.assertNotEqual(run21["loader"]["sha256"],
                            data["dma_e820_build"]["loader"]["sha256"])
        self.assertEqual(run21["loader"]["wifi_firmware_dump"]["bytes"],
                         data["ubuntu_wifi"]["firmware"]["size"])
        self.assertEqual(run21["wifi"]["firmware"]["sha256"],
                         data["ubuntu_wifi"]["firmware"]["sha256"])
        self.assertTrue(run21["loader"]["wake_copy"]["inside_proven_window"])
        self.assertEqual(run21["wake"]["seconds_wake_to_tcp22"], 25)
        self.assertEqual(run21["observed_e820"]["reserved"],
                         data["dma_e820_build"]["observed_e820"]["reserved"])
        self.assertEqual(run21["kaslr"]["kernel_code_physical_start"], "0x26ec00000")
        self.assertEqual(run21["mem_total_kib"], 14788356)
        self.assertTrue(run21["physical_display_observed"])
        self.assertTrue(run21["vcn"]["vcn_initialized"])
        self.assertFalse(run21["vcn"]["decode_tested"])
        self.assertTrue(run21["wifi"]["joined"])
        self.assertFalse(run21["bluetooth_working"])
        self.assertTrue(run21["dualsense_usb"])
        self.assertFalse(run21["thermal"]["frequency_drivers_autoloaded"])
        install = run21["large_install_observation"]
        self.assertEqual(install["download_bytes"], 53229366208)
        self.assertFalse(install["manual_steam_integrity_check"])
        self.assertFalse(install["independent_readback_or_hash_check"])
        self.assertEqual(install["watcher"]["samples"], 480)
        self.assertFalse(
            install["watcher"]["throughput_and_total_counters_valid"])
        game_load = run21["game_load_observation"]
        self.assertEqual(game_load["samples"], 540)
        self.assertEqual(game_load["gpu_peak_mhz"], 2230)
        self.assertEqual(game_load["temperature_peak_c"], 84.0)
        self.assertTrue(game_load["logger_ended_while_load_active"])
        self.assertFalse(game_load["operator_confirmed_gameplay"])
        self.assertFalse(game_load["thermal_equilibrium_established"])
        self.assertTrue(run21["game_load_telemetry_recorded"])
        self.assertEqual(len(run21["pending"]), 3)
        followup = run21["post_run21_image_followup"]
        self.assertEqual(len(followup["included_in_ci_build_2_source"]), 5)
        self.assertEqual(len(followup["unresolved_after_ci_build_2_source"]), 2)
        self.assertFalse(run21["gaming_load_tested"])
        self.assertFalse(run21["release_loader_baseline"])
        self.assertTrue(
            data["sonic_display_diagnostics"]["run15"]["release_loader_baseline"])
        self.assertEqual(data["dma_e820_build"]["run"], 18)
        self.assertEqual(data["ubuntu_ci_dma_run"]["run"], 19)
        self.assertEqual(
            data["latest_authenticated_working_run_scope"],
            "numbered-regular-console-run-only",
        )
        self.assertEqual(data["latest_tested_run"], "ps5-pro-linux-test3-pass")

    def test_manifest_records_public_image3_hardware_result(self):
        data = load_pinned_manifest()
        run21 = data["cachyos_k73_run"]
        image3 = run21["ci_build_3_public_prerelease"]
        self.assertEqual(
            image3["source_commit"],
            "16795eb85830dc32f712e44e9e0da28f7874b317",
        )
        self.assertTrue(image3["booted"])
        self.assertFalse(image3["hardware_result_transfers_from_local_image"])
        hardware = image3["hardware_test"]
        self.assertEqual(hardware["boot_count"], 1)
        self.assertTrue(hardware["identity"]["whole_device_readback_sha256_match"])
        self.assertTrue(hardware["boot"]["physical_hdmi"])
        self.assertTrue(hardware["wifi"]["gui_join"])
        self.assertTrue(hardware["bluetooth"]["dualsense_paired"])
        self.assertFalse(hardware["bluetooth"]["cold_boot_reconnect_tested"])
        self.assertTrue(hardware["sessions"]["plasma_to_gaming_mode"])
        self.assertTrue(hardware["sessions"]["gaming_mode_to_plasma"])
        self.assertFalse(hardware["fan"]["live_hotfix_in_release"])
        self.assertFalse(
            hardware["bounded_cpu_load"]["thermal_equilibrium_tested"])

        followup = run21["current_image3_source_followup"]
        self.assertEqual(
            followup["source_commit"],
            "d9c4b31f30193e60e79723d4543b2a85941c315a",
        )
        self.assertEqual(
            followup["release_source_commit"], image3["source_commit"])
        self.assertTrue(followup["hosted_artifact_hardware_tested"])
        self.assertTrue(followup["networkmanager_polkit_hardware_tested_live"])
        self.assertTrue(followup["networkd_wait_online_masked_before_first_boot"])
        self.assertFalse(followup["current_source_artifact_hardware_tested"])

    def test_run21_summary_separates_image2_changes_from_unresolved_behavior(self):
        summary = (ROOT / "evidence" / "11.60-summary.txt").read_text()
        self.assertNotIn("cachyos_k73_run.fix_for_ci_build_2_", summary)
        expected = (
            "cachyos_k73_run.post_run21_image_followup.included_1=iw620-bluetooth-quirk-ordering-followup-after-rmux-base",
            "cachyos_k73_run.post_run21_image_followup.included_2=iw620-firmware-before-explicit-driver-load",
            "cachyos_k73_run.post_run21_image_followup.included_3=linux-ps5-7.3.0-2-kbuild-build-version-2",
            "cachyos_k73_run.post_run21_image_followup.included_4=frequency-drivers-manual-only",
            "cachyos_k73_run.post_run21_image_followup.included_5=ps5fan-enabled-fixed-maximum-pattern-3-not-dynamic-curve",
            "cachyos_k73_run.post_run21_image_followup.unresolved_1=steam-switch-to-desktop",
            "cachyos_k73_run.post_run21_image_followup.unresolved_2=kde-network-menu-wifi-join",
            "cachyos_k73_run.ci_build_2_workflow_conclusion=success",
            "cachyos_k73_run.ci_build_2_ci_result_verified=true",
            "cachyos_k73_run.ci_build_2_release_policy=public-prerelease-for-hardware-testing",
            "cachyos_k73_run.ci_build_2_release_is_draft=false",
            "cachyos_k73_run.ci_build_2_release_is_prerelease=true",
            "cachyos_k73_run.ci_build_2_published_for_testing=true",
            "cachyos_k73_run.ci_build_2_asset_size=1943471712",
            "cachyos_k73_run.ci_build_2_asset_sha256=8b785243f79a32a4155cc1e39bed01d580e25ca514e88abbfed1a8a8157a281a",
            "cachyos_k73_run.ci_build_2_raw_size=12582912000",
            "cachyos_k73_run.ci_build_2_raw_sha256=3798c7dba96412c5301eb201d8bf8aa4edd1b2f80a743dfd7b90b2a79222c62d",
        )
        for line in expected:
            with self.subTest(line=line):
                self.assertIn(f"{line}\n", summary)

    def test_manifest_requires_run21_record(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_pinned_manifest()
            del data["cachyos_k73_run"]
            path.write_text(json.dumps(data))
            errors = validate(path)
            self.assertTrue(any("missing cachyos_k73_run" in error
                                for error in errors))
            self.assertTrue(any("cachyos_k73_run is not an object" in error
                                for error in errors))

    def test_manifest_requires_run21_upstream_credit(self):
        for field in ("author", "repository"):
            with self.subTest(field=field), TemporaryDirectory() as temp:
                path = Path(temp) / "manifest.json"
                data = load_pinned_manifest()
                del data["cachyos_k73_run"]["upstream_kernel_work"][field]
                path.write_text(json.dumps(data))
                self.assertTrue(any("Run 21 must credit rmux" in error
                                    for error in validate(path)))

    def test_manifest_rejects_run21_loader_hash_drift(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_pinned_manifest()
            data["cachyos_k73_run"]["loader"]["sha256"] = (
                "2e1758a2d013305bcb9faa0eb3adf18c34ed76ad85313dd945719c8bf2a0c9c0"
            )
            path.write_text(json.dumps(data))
            errors = validate(path)
            self.assertTrue(any("unexpected Run 21 loader SHA-256" in error
                                for error in errors))
            self.assertTrue(any("Run 21 loader must differ from the Run 18 DMA loader"
                                in error for error in errors))

    def test_manifest_rejects_run21_loader_prerelease_drift(self):
        cases = (
            (("release_is_draft",), True,
             "unexpected Run 21 loader prerelease state"),
            (("release_is_prerelease",), False,
             "unexpected Run 21 loader prerelease state"),
            (("release_assets", "bounded_wifi", "hardware_booted"), False,
             "unexpected bounded Wi-Fi release asset"),
            (("release_assets", "bounded_non_wifi", "hardware_booted"), True,
             "unexpected bounded non-Wi-Fi release asset"),
        )
        for keys, value, message in cases:
            with self.subTest(keys=keys), TemporaryDirectory() as temp:
                path = Path(temp) / "manifest.json"
                data = load_pinned_manifest()
                target = data["cachyos_k73_run"]["loader"]
                for key in keys[:-1]:
                    target = target[key]
                target[keys[-1]] = value
                path.write_text(json.dumps(data))
                self.assertTrue(any(message in error for error in validate(path)))

    def test_manifest_rejects_run21_release_baseline_claim(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_pinned_manifest()
            data["sonic_display_diagnostics"]["release"]["elf_sha256"] = (
                data["cachyos_k73_run"]["loader"]["sha256"])
            path.write_text(json.dumps(data))
            self.assertTrue(any("Run 15 must remain the release loader ELF" in error
                                for error in validate(path)))

    def test_manifest_rejects_run21_image_drift(self):
        cases = (
            (("raw", "sha256"), "0" * 64, "unexpected Run 21 image SHA-256"),
            (("built_by_ci",), True, "Run 21 booted a local image build"),
        )
        for keys, value, message in cases:
            with self.subTest(keys=keys), TemporaryDirectory() as temp:
                path = Path(temp) / "manifest.json"
                data = load_pinned_manifest()
                target = data["cachyos_k73_run"]["image"]
                for key in keys[:-1]:
                    target = target[key]
                target[keys[-1]] = value
                path.write_text(json.dumps(data))
                self.assertTrue(any(message in error for error in validate(path)))

    def test_manifest_rejects_run21_later_ci_state_drift(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_pinned_manifest()
            data["cachyos_k73_run"]["later_ci_build"]["workflow_conclusion"] = "failure"
            path.write_text(json.dumps(data))
            self.assertTrue(any("Run 21 later CI build" in error
                                for error in validate(path)))

    def test_manifest_rejects_cachyos_image2_identity_drift(self):
        cases = (
            ("source_commit", "0" * 40, "unexpected CachyOS image 2 source identity"),
            ("booted", True,
             "CachyOS image 2 prerelease or boot state is overstated"),
            ("release_is_draft", True,
             "CachyOS image 2 prerelease or boot state is overstated"),
            ("release_is_prerelease", False,
             "CachyOS image 2 prerelease or boot state is overstated"),
        )
        for field, value, message in cases:
            with self.subTest(field=field), TemporaryDirectory() as temp:
                path = Path(temp) / "manifest.json"
                data = load_pinned_manifest()
                data["cachyos_k73_run"]["ci_build_2"][field] = value
                path.write_text(json.dumps(data))
                self.assertTrue(any(message in error for error in validate(path)))

    def test_manifest_rejects_cachyos_image2_patch_or_package_drift(self):
        cases = (
            (("kernel_package", "version"), "7.3.0-1",
             "unexpected CachyOS image 2 kernel package identity"),
            (("base_patch_set", "used_as_published"), False,
             "CachyOS image 2 must use the pinned rmux base patch"),
            (("bluetooth_followup_patch", "hardware_tested"), True,
             "unexpected CachyOS image 2 Bluetooth follow-up"),
            (("bluetooth_followup_patch", "external_confirmation",
              "byte_identical_patch"), True,
             "unexpected image 2 Bluetooth external confirmation"),
            (("fan_policy", "dynamic_temperature_curve"), True,
             "unexpected CachyOS image 2 fan policy"),
        )
        for keys, value, message in cases:
            with self.subTest(keys=keys), TemporaryDirectory() as temp:
                path = Path(temp) / "manifest.json"
                data = load_pinned_manifest()
                target = data["cachyos_k73_run"]["ci_build_2"]
                for key in keys[:-1]:
                    target = target[key]
                target[keys[-1]] = value
                path.write_text(json.dumps(data))
                self.assertTrue(any(message in error for error in validate(path)))

    def test_manifest_rejects_split_or_incorrect_image2_asset_claim(self):
        cases = (
            ("expected_image_asset_count", 2,
             "CachyOS image 2 must be one unsplit .img.xz"),
            ("size", 1,
             "unexpected CachyOS image 2 release asset identity"),
            ("verified", False,
             "unexpected CachyOS image 2 release asset identity"),
        )
        for field, value, message in cases:
            with self.subTest(field=field), TemporaryDirectory() as temp:
                path = Path(temp) / "manifest.json"
                data = load_pinned_manifest()
                data["cachyos_k73_run"]["ci_build_2"][
                    "release_asset_policy"][field] = value
                path.write_text(json.dumps(data))
                self.assertTrue(any(message in error for error in validate(path)))

    def test_manifest_accepts_verified_image2_ci_and_asset_metadata(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_pinned_manifest()
            path.write_text(json.dumps(data))
            self.assertEqual(validate(path), [])

    def test_manifest_rejects_incorrect_image2_raw_image_identity(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_pinned_manifest()
            data["cachyos_k73_run"]["ci_build_2"]["raw_image"]["size"] = 1
            path.write_text(json.dumps(data))
            self.assertTrue(any(
                "unexpected CachyOS image 2 raw image identity" in error
                for error in validate(path)
            ))

    def test_manifest_rejects_run21_boot_file_drift(self):
        cases = (
            ("bzimage", "size", 12702720, "Run 21 boot file bzimage size"),
            ("initrd", "sha256", "0" * 64, "Run 21 boot file initrd SHA-256"),
        )
        for name, field, value, message in cases:
            with self.subTest(name=name), TemporaryDirectory() as temp:
                path = Path(temp) / "manifest.json"
                data = load_pinned_manifest()
                data["cachyos_k73_run"]["boot_files"][name][field] = value
                path.write_text(json.dumps(data))
                self.assertTrue(any(message in error for error in validate(path)))

    def test_manifest_rejects_run21_wifi_firmware_drift(self):
        cases = (
            (("loader", "wifi_firmware_dump", "bytes"), 498109,
             "Run 21 loader Wi-Fi firmware dump size disagrees"),
            (("wifi", "firmware", "sha256"), "0" * 64,
             "Run 21 Wi-Fi firmware must be the Run 17 p47 blob"),
        )
        for keys, value, message in cases:
            with self.subTest(keys=keys), TemporaryDirectory() as temp:
                path = Path(temp) / "manifest.json"
                data = load_pinned_manifest()
                target = data["cachyos_k73_run"]
                for key in keys[:-1]:
                    target = target[key]
                target[keys[-1]] = value
                path.write_text(json.dumps(data))
                self.assertTrue(any(message in error for error in validate(path)))

    def test_manifest_rejects_run21_wake_copy_outside_window(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_pinned_manifest()
            data["cachyos_k73_run"]["loader"]["wake_copy"]["end"] = "0x104100000"
            path.write_text(json.dumps(data))
            self.assertTrue(any("Run 21 wake copy must stay inside the proven window"
                                in error for error in validate(path)))

    def test_manifest_rejects_wrong_run21_memory_layout(self):
        cases = (
            ("observed_e820", "reserved", "start", "0x000000003fffc000",
             "unexpected Run 21 observed e820 reserved range"),
            ("kaslr", None, "kernel_code_physical_start", "0x2000000",
             "Run 21 kernel must sit above the reserved range"),
        )
        for outer, inner, field, value, message in cases:
            with self.subTest(outer=outer), TemporaryDirectory() as temp:
                path = Path(temp) / "manifest.json"
                data = load_pinned_manifest()
                target = data["cachyos_k73_run"][outer]
                if inner is not None:
                    target = target[inner]
                target[field] = value
                path.write_text(json.dumps(data))
                self.assertTrue(any(message in error for error in validate(path)))

    def test_manifest_requires_run21_display_observation(self):
        for target in ("run", "display"):
            with self.subTest(target=target), TemporaryDirectory() as temp:
                path = Path(temp) / "manifest.json"
                data = load_pinned_manifest()
                run21 = data["cachyos_k73_run"]
                if target == "run":
                    run21["physical_display_observed"] = False
                else:
                    run21["display"]["direct_operator_observation"] = False
                path.write_text(json.dumps(data))
                self.assertTrue(any("Run 21 must record the directly observed display"
                                    in error for error in validate(path)))

    def test_manifest_rejects_run21_device_overstatement(self):
        cases = (
            (("vcn", "decode_tested"), True,
             "Run 21 VCN must be initialized with decode not tested"),
            (("bluetooth_working",), True, "Run 21 Bluetooth is overstated"),
            (("thermal", "frequency_drivers_autoloaded"), True,
             "Run 21 frequency driver autoload is overstated"),
        )
        for keys, value, message in cases:
            with self.subTest(keys=keys), TemporaryDirectory() as temp:
                path = Path(temp) / "manifest.json"
                data = load_pinned_manifest()
                target = data["cachyos_k73_run"]
                for key in keys[:-1]:
                    target = target[key]
                target[keys[-1]] = value
                path.write_text(json.dumps(data))
                self.assertTrue(any(message in error for error in validate(path)))

    def test_manifest_rejects_run21_thermal_drift(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_pinned_manifest()
            data["cachyos_k73_run"]["thermal"]["steps"][1]["settled_c"] = [30.0, 31.0]
            path.write_text(json.dumps(data))
            self.assertTrue(any("unexpected Run 21 thermal steps" in error
                                for error in validate(path)))

    def test_manifest_rejects_run21_large_install_drift(self):
        cases = (
            (("download_bytes",), 0,
             "unexpected Run 21 large-install observation"),
            (("manual_steam_integrity_check",), True,
             "unexpected Run 21 large-install observation"),
            (("watcher", "throughput_and_total_counters_valid"), True,
             "unexpected Run 21 storage-watcher observation"),
            (("watcher", "diskstats_fields_used"), [6, 10],
             "unexpected Run 21 storage-watcher observation"),
        )
        for keys, value, message in cases:
            with self.subTest(keys=keys), TemporaryDirectory() as temp:
                path = Path(temp) / "manifest.json"
                data = load_pinned_manifest()
                target = data["cachyos_k73_run"]["large_install_observation"]
                for key in keys[:-1]:
                    target = target[key]
                target[keys[-1]] = value
                path.write_text(json.dumps(data))
                self.assertTrue(any(message in error for error in validate(path)))

    def test_manifest_rejects_run21_game_load_drift(self):
        cases = (
            ("samples", 539),
            ("temperature_peak_c", 80.0),
            ("operator_confirmed_gameplay", True),
            ("thermal_equilibrium_established", True),
        )
        for field, value in cases:
            with self.subTest(field=field), TemporaryDirectory() as temp:
                path = Path(temp) / "manifest.json"
                data = load_pinned_manifest()
                data["cachyos_k73_run"]["game_load_observation"][field] = value
                path.write_text(json.dumps(data))
                self.assertTrue(any("unexpected Run 21 game-load observation" in error
                                    for error in validate(path)))

    def test_manifest_requires_run21_game_load_telemetry_marker(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_pinned_manifest()
            data["cachyos_k73_run"]["game_load_telemetry_recorded"] = False
            path.write_text(json.dumps(data))
            self.assertTrue(any("Run 21 game-load telemetry is missing" in error
                                for error in validate(path)))

    def test_manifest_requires_run21_pending_checks(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = load_pinned_manifest()
            data["cachyos_k73_run"]["pending"] = []
            path.write_text(json.dumps(data))
            self.assertTrue(any("Run 21 must list the three remaining checks" in error
                                for error in validate(path)))

    def test_manifest_rejects_overstated_run21_scope(self):
        for field in ("independent_hardware_reproduction", "ab_control_run",
                      "tester_errors_reproduced", "soak_tested",
                      "gaming_load_tested", "ci_built_image"):
            with self.subTest(field=field), TemporaryDirectory() as temp:
                path = Path(temp) / "manifest.json"
                data = load_pinned_manifest()
                data["cachyos_k73_run"][field] = True
                path.write_text(json.dumps(data))
                self.assertTrue(any(f"Run 21 {field} is overstated" in error
                                    for error in validate(path)))


if __name__ == "__main__":
    unittest.main()
