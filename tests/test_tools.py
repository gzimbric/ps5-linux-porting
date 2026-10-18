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
        self.assertEqual(data["latest_authenticated_working_run"], 16)
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
            data["latest_authenticated_working_run"] = 15
            path.write_text(json.dumps(data))
            self.assertTrue(any("latest authenticated working run" in error
                                for error in validate(path)))


if __name__ == "__main__":
    unittest.main()
