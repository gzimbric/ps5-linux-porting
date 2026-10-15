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

    def test_public_tree_rejects_binary(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "payload.elf").write_bytes(b"x")
            self.assertTrue(check_public_tree(root))

    def test_manifest_rejects_invalid_candidate_digest(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            data = json.loads((ROOT / "firmwares" / "11.60.json").read_text())
            data["candidate_build"]["sha256"]["final_elf"] = "not-a-digest"
            path.write_text(json.dumps(data))
            self.assertTrue(any("candidate SHA-256" in error
                                for error in validate(path)))


if __name__ == "__main__":
    unittest.main()
