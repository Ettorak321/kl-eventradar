import unittest
from datetime import date, timedelta

from scripts.event_series import collapse_adjacent_series


def event(day, **kwargs):
    row = {"id": "city-" + day.isoformat(), "title": "Lautrer Weihnachtsmarkt",
           "start": day.isoformat() + "T10:00:00+01:00", "end": None,
           "allDay": False, "category": "markt", "eventType": "Markt / Messe",
           "sourceKey": "city", "location": "Stiftskirche und Schillerplatz",
           "region": "stadt-kl", "locality": "Kaiserslautern",
           "status": "confirmed",
           "source": "https://www.kaiserslautern.de/?day=" + day.isoformat()}
    row.update(kwargs)
    return row


class SeriesTests(unittest.TestCase):
    def test_realistic_lautrer_market_keeps_closed_day_gap(self):
        # Der 22.11.2026 fehlt in den veröffentlichten Einträgen.
        start, end = date(2026, 11, 16), date(2026, 12, 23)
        original = [event(start + timedelta(days=i)) for i in range((end - start).days + 1)
                    if start + timedelta(days=i) != date(2026, 11, 22)]
        original[12]["start"] = original[12]["start"].replace("10:00:00", "13:00:00")
        combined = collapse_adjacent_series(original)
        self.assertEqual(len(original), 37)
        self.assertEqual(len(combined), 2)
        a, b = combined
        self.assertEqual((a["start"], a["end"], a["seriesCount"]), ("2026-11-16", "2026-11-22", 6))
        self.assertEqual((b["start"], b["end"], b["seriesCount"]), ("2026-11-23", "2026-12-24", 31))
        self.assertEqual(sum(len(x["seriesDays"]) for x in combined), 37)
        self.assertTrue(all(x["allDay"] and x["isSeries"] for x in combined))
        self.assertTrue(any("13:00:00" in d["start"] for d in b["seriesDays"]))
        self.assertTrue(all(d["source"].startswith("https://") for x in combined for d in x["seriesDays"]))
        self.assertFalse(any(d["date"] == "2026-11-22" for x in combined for d in x["seriesDays"]))
        self.assertEqual(combined, collapse_adjacent_series(original))

    def test_different_places_titles_and_sources_do_not_merge(self):
        base = date(2026, 12, 1)
        rows = [event(base), event(base+timedelta(days=1), location="Anderer Platz"),
                event(base+timedelta(days=2), title="Anderer Weihnachtsmarkt"),
                event(base+timedelta(days=3), sourceKey="weilerbach")]
        self.assertEqual(len(collapse_adjacent_series(rows)), 4)

    def test_daily_performances_not_merged(self):
        d = date(2026, 12, 1)
        self.assertEqual(len(collapse_adjacent_series([
            event(d, category="konzert"), event(d+timedelta(days=1), category="konzert")
        ])), 2)

    def test_separate_program_text_and_status_remain_separate(self):
        d = date(2026, 12, 1)
        rows = [event(d), event(d+timedelta(days=1), description="Sonderprogramm"),
                event(d+timedelta(days=2), status="tentative")]
        self.assertEqual(len(collapse_adjacent_series(rows)), 3)

    def test_already_multiday_and_future_predictions_unchanged(self):
        d = date(2026, 12, 1)
        original = [event(d, allDay=True, start="2026-12-01", end="2026-12-05"),
                    event(d+timedelta(days=1), forecast=True)]
        self.assertEqual(collapse_adjacent_series(original), original)

    def test_multiple_same_day_not_combined(self):
        d=date(2026, 11, 30)
        rows = [event(d, id="morning"),event(d, id="evening",
            start="2026-11-30T18:00:00+01:00"),event(d+timedelta(days=1))]
        self.assertEqual(len(collapse_adjacent_series(rows)), 3)

    def test_single_day_untouched(self):
        x=event(date(2026, 12, 1))
        self.assertEqual(collapse_adjacent_series([x]), [x])

    def test_series_not_merged_again(self):
        d=date(2026,12,1)
        first=collapse_adjacent_series([event(d),event(d+timedelta(days=1))])
        self.assertEqual(collapse_adjacent_series(first),first)


if __name__=="__main__":
    unittest.main()
