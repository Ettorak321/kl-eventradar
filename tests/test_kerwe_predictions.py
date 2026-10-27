import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from scripts import kerwe_predictions as kp


class TestKerwePredictions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = kp.load_rules()

    def test_three_sourced_rules(self):
        self.assertEqual(len(self.rules), 3)
        self.assertTrue(all(len(r["evidence"]) >= 2 for r in self.rules))

    def test_four_future_years(self):
        events = kp.create_forecasts([], self.rules, today=date(2026, 10, 27))
        self.assertEqual(len(events), 12)
        by_id = {e["id"]: e for e in events}
        self.assertEqual(by_id["kerwe-vorschau-rodenbach-kerwe-2027"]["start"], "2027-09-03")
        self.assertEqual(by_id["kerwe-vorschau-mackenbach-kerwe-2027"]["start"], "2027-09-10")
        self.assertEqual(by_id["kerwe-vorschau-weilerbach-kerwe-2027"]["start"], "2027-09-24")
        self.assertEqual(by_id["kerwe-vorschau-weilerbach-kerwe-2027"]["end"], "2027-09-28")
        self.assertTrue(all(e["status"] == "predicted" and not e["isStadium"] for e in events))

    def test_official_date_replaces_prediction_even_if_different(self):
        official = {"title": "Kerwe in Rodenbach", "start": "2027-09-17",
                    "region": "vg-weilerbach", "locality": "Rodenbach",
                    "location": "Dorfplatz Rodenbach", "sourceKey": "weilerbach"}
        ids = {e["id"] for e in kp.create_forecasts([official], self.rules, today=date(2026, 10, 27))}
        self.assertNotIn("kerwe-vorschau-rodenbach-kerwe-2027", ids)
        self.assertIn("kerwe-vorschau-rodenbach-kerwe-2028", ids)

    def test_other_village_does_not_replace(self):
        official = {"title": "Kerwe in Mackenbach", "start": "2027-09-10",
                    "region": "vg-weilerbach", "locality": "Mackenbach",
                    "location": "Mackenbach", "sourceKey": "weilerbach"}
        ids = {e["id"] for e in kp.create_forecasts([official], self.rules, today=date(2026, 10, 27))}
        self.assertIn("kerwe-vorschau-rodenbach-kerwe-2027", ids)
        self.assertNotIn("kerwe-vorschau-mackenbach-kerwe-2027", ids)

    def test_old_prediction_recomputed(self):
        prior = [{"id": "alt", "sourceKey": "kerwe_forecast", "forecast": True, "start": "2025-09-01"}]
        self.assertNotIn("alt", {e["id"] for e in kp.attach_forecasts(prior, today=date(2026, 10, 27))})

    def test_missing_or_bad_rules(self):
        with tempfile.TemporaryDirectory() as root:
            p = Path(root) / "rules.json"
            self.assertEqual(kp.attach_forecasts([], rules_path=p, today=date(2026, 10, 27)), [])
            p.write_text(json.dumps({"schemaVersion": 2, "rules": []}), encoding="utf-8")
            with self.assertRaises(ValueError):
                kp.attach_forecasts([], rules_path=p, today=date(2026, 10, 27))

    def test_2024_exception_disclosed(self):
        row = next(r for r in self.rules if r["id"] == "mackenbach-kerwe")
        self.assertTrue(any(x["year"] == 2024 for x in row["exceptions"]))


if __name__ == "__main__":
    unittest.main()
