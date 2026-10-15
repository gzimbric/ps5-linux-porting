from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

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

    def test_links(self):
        self.assertEqual(check_links(ROOT), [])

    def test_public_tree(self):
        self.assertEqual(check_public_tree(ROOT), [])

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
            data["checkpoints"]["syscore_alias_read_through"] = True
            path.write_text(json.dumps(data))
            self.assertTrue(any("syscore read-through disagrees" in error
                                for error in validate(path)))


if __name__ == "__main__":
    unittest.main()
