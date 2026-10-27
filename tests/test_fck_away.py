import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from scripts import fetch_events as fe
from scripts.event_taxonomy import relabel

FIXTURE = Path(__file__).parent / "fixtures" / "fck_mixed.ics"

class AwayGameTests(unittest.TestCase):
    def test_classification(self):
        self.assertEqual(fe.fixture_kind("Hannover 96 - 1. FC Kaiserslautern", "Hannover"), "away")
        self.assertEqual(fe.fixture_kind("1. FC Kaiserslautern - Hannover 96", "Fritz-Walter-Stadion"), "home")
        self.assertIsNone(fe.fixture_kind("1. FC Kaiserslautern - Hannover 96", ""))
        self.assertIsNone(fe.fixture_kind("Hannover 96 - 1. FC Kaiserslautern", "Fritz-Walter-Stadion"))
    def test_mixed_feed_keeps_home_and_away(self):
        with patch.object(fe, "fetch", return_value=SimpleNamespace(content=FIXTURE.read_bytes())):
            rows=fe.parse_fck_ics("https://example.invalid")
        self.assertEqual(len(rows),2)
        home=next(x for x in rows if x["isStadium"])
        away=next(x for x in rows if x["isAway"])
        self.assertTrue(home["venueVerified"])
        self.assertFalse(away["isStadium"])
        self.assertEqual(relabel(away)["category"],"fck_auswaerts")
        self.assertNotIn("Fritz-Walter-Stadion",away["location"])
    def test_official_vs_format(self):
        self.assertEqual(fe.fixture_kind("FCK vs. Fortuna Düsseldorf | 28. Spieltag","Fritz-Walter-Stadion"),"home")
        self.assertEqual(fe.fixture_kind("Hannover 96 vs. FCK | 29. Spieltag","Heinz von Heiden Arena"),"away")

if __name__ == "__main__":
    unittest.main()
