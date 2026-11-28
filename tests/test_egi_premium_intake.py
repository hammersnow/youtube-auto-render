import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import egi_approved_assets as assets
import render_egi_daily as renderer
import egi_release_gate as gate

def candidate():
    a = {"tag":"egi-approved-egi-test-premium", "file":"EGI_Test_Premium.mp4",
         "sha256":"a"*64, "source_commit":"b"*40, "source_run":1,
         "source_artifact":2, "artifact_name":"test-native-preview",
         "duration_seconds":16, "fps":30, "width":1080, "height":1920,
         "native_frames":480}
    a["review"] = {"status":"approved", "authority":"reviewer-integrator",
                   "reviewed_sha256":a["sha256"], "source_commit":a["source_commit"],
                   "evidence":"TEST FIXTURE ONLY; this is not a real approval or publication."}
    a["review"].update({k:True for k in assets.GATES})
    return {"id":"egi-test-premium", "category":"technology", "renderer":assets.RENDERER,
            "title":"Test only #Shorts", "description":"Test #EGI", "tags":["test"], "approved_asset":a}

class GateTests(unittest.TestCase):
    def setUp(self):
        self.cat = json.loads((ROOT/"config/egi_episode_catalog.json").read_text())
        self.e = candidate()
        self.day = "2099-01-01"
        self.cat["schedule"][self.day] = [self.e]

    def test_historical_and_generic(self):
        self.assertIn(self.e["id"], renderer.check_catalog(self.cat))

    def test_reject_review_missing(self):
        self.e["approved_asset"]["review"]["full_audio_review"] = False
        with self.assertRaises(AssertionError): renderer.check_catalog(self.cat)

    def test_reject_hash_mismatch(self):
        self.e["approved_asset"]["review"]["reviewed_sha256"] = "c"*64
        with self.assertRaises(AssertionError): renderer.check_catalog(self.cat)

    def test_reject_unsafe_path(self):
        self.e["approved_asset"]["file"] = "../bad.mp4"
        with self.assertRaises(AssertionError): renderer.check_catalog(self.cat)

    def test_reject_downgrade(self):
        self.e["approved_asset"]["fps"] = 12
        with self.assertRaises(AssertionError): renderer.check_catalog(self.cat)

    def test_reject_duplicate_hash_across_dates(self):
        other = copy.deepcopy(self.e)
        other["id"] = "egi-test-other"
        other["approved_asset"]["tag"] = "egi-approved-egi-test-other"
        self.cat["schedule"]["2099-01-02"] = [other]
        with self.assertRaises(AssertionError): renderer.check_catalog(self.cat)

    def test_release_exact_hash(self):
        a = self.e["approved_asset"]
        m = {"date":self.day,"brand":"EGI","strategy":"egi-premium-v16","publish_enabled":True,
             "timezone":"Europe/Istanbul","shorts":[{"episode_id":self.e["id"],"file":a["file"],
             "sha256":a["sha256"],"title":self.e["title"]}]}
        files = {"assets":[{"name":a["file"],"size":400000},{"name":"manifest.json","size":1200}]}
        self.assertTrue(gate.release_ready(self.day,self.cat,m,files))
        m["shorts"][0]["sha256"] = "c"*64
        self.assertFalse(gate.release_ready(self.day,self.cat,m,files))

    def test_reject_duplicate_day_filename(self):
        other=copy.deepcopy(self.e)
        other["id"]="egi-test-other"
        other["approved_asset"]["tag"]="egi-approved-egi-test-other"
        other["approved_asset"]["sha256"]="c"*64
        other["approved_asset"]["review"]["reviewed_sha256"]="c"*64
        self.cat["schedule"][self.day].append(other)
        with self.assertRaises(AssertionError): renderer.check_catalog(self.cat)

if __name__ == "__main__":
    unittest.main()
