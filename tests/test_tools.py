import hashlib
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.check_links import check as check_links
from tools.check_public_tree import check as check_public_tree
from tools.classify_1160_log import classify
from tools.validate_manifests import validate


ROOT = Path(__file__).resolve().parents[1]


class ToolTests(unittest.TestCase):
    def test_manifest(self):
        self.assertEqual(validate(ROOT / "firmwares" / "11.60.json"), [])
        data = json.loads((ROOT / "firmwares" / "11.60.json").read_text())
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
        self.assertTrue(run15["last_authenticated_working_baseline"])
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
        self.assertEqual(
            data["boot_media"]["initrd"]["sha256"],
            "c37b88569ef8f05b0b4ae432a8ec0fd323b7a3537a6441f8c45baaad45ff061f",
        )

    def test_links(self):
        self.assertEqual(check_links(ROOT), [])

    def test_public_tree(self):
        self.assertEqual(check_public_tree(ROOT), [])

    def test_run15_amdgpu_config(self):
        path = ROOT / "config" / "ps5-amdgpu.conf"
        self.assertEqual(
            hashlib.sha256(path.read_bytes()).hexdigest(),
            "51dbae6f372fa1f5bceee2fd95403042bb6954d29b3f9db2a11c769dd41fc677",
        )
        self.assertEqual(path.stat().st_size, 195)

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

    def test_manifest_rejects_invalid_candidate_digest(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = json.loads((ROOT / "firmwares" / "11.60.json").read_text())
            data["superseded_candidate_build"]["sha256"]["final_elf"] = "not-a-digest"
            path.write_text(json.dumps(data))
            self.assertTrue(any("candidate SHA-256" in error
                                for error in validate(path)))

    def test_manifest_requires_bounded_diagnostics(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = json.loads((ROOT / "firmwares" / "11.60.json").read_text())
            del data["bounded_loader_diagnostics"]
            path.write_text(json.dumps(data))
            self.assertTrue(any("bounded_loader_diagnostics" in error
                                for error in validate(path)))

    def test_manifest_rejects_invalid_bounded_stage_hash(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = json.loads((ROOT / "firmwares" / "11.60.json").read_text())
            data["bounded_loader_diagnostics"]["stage1"]["sha256"] = "bad"
            path.write_text(json.dumps(data))
            self.assertTrue(any("bounded stage1 SHA-256" in error
                                for error in validate(path)))

    def test_manifest_rejects_bounded_count_drift(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = json.loads((ROOT / "firmwares" / "11.60.json").read_text())
            data["bounded_loader_diagnostics"]["stage1"]["leaf_ptes"] -= 1
            path.write_text(json.dumps(data))
            self.assertTrue(any("inconsistent bounded stage1 counts" in error
                                for error in validate(path)))

    def test_manifest_rejects_false_alias_readthrough(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = json.loads((ROOT / "firmwares" / "11.60.json").read_text())
            data["checkpoints"]["syscore_alias_read_through"] = False
            path.write_text(json.dumps(data))
            self.assertTrue(any("syscore read-through disagrees" in error
                                for error in validate(path)))

    def test_manifest_rejects_executed_stage2a(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = json.loads((ROOT / "firmwares" / "11.60.json").read_text())
            data["bounded_loader_diagnostics"]["stage2a"]["executed"] = True
            path.write_text(json.dumps(data))
            self.assertTrue(any("stage2a requires executed=false" in error
                                for error in validate(path)))

    def test_manifest_rejects_overstated_display_telemetry(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = json.loads((ROOT / "firmwares" / "11.60.json").read_text())
            data["checkpoints"]["individual_mp3_and_table_returns_observed"] = True
            path.write_text(json.dumps(data))
            self.assertTrue(any("return scope is overstated" in error
                                for error in validate(path)))


if __name__ == "__main__":
    unittest.main()
