import unittest
from datetime import date, timedelta
from scripts.exhibition_series import annotate_exhibition_series
from scripts.event_series import collapse_adjacent_series


def make(day, title, venue, **overrides):
    item = {"id": f"{title}-{day.isoformat()}", "sourceKey": "city",
            "title": title, "location": venue, "start": day.isoformat()+"T10:00:00+01:00",
            "end": None, "allDay": False, "category": "sonstiges",
            "eventType": "Sonstiges", "region": "stadt-kl",
            "locality": "Kaiserslautern", "description": "",
            "status": "confirmed", "source": "https://example.org/kalender"}
    item.update(overrides)
    return item


class ExhibitionSeriesTests(unittest.TestCase):
    def test_three_real_exhibition_patterns_without_mondays(self):
        patterns = [
            ("Hans Purrmann als Sammler", "mpk - Museum Pfalzgalerie Kaiserslautern",
             date(2026, 11, 3), 6),
            ("Die Goldenen Zwanziger in Kaiserslautern: Nicht alles Gold, was glänzt?",
             "Stadtmuseum Kaiserslautern", date(2026, 11, 4), 5),
            ("Neues von PFAFF", "Stadtmuseum Kaiserslautern", date(2026, 11, 4), 5),
            ("Eileen Gray: Golden Girls No. 3",
             "mpk - Museum Pfalzgalerie Kaiserslautern", date(2026, 11, 3), 6),
        ]
        raw = [make(start+timedelta(days=i), name, place)
               for name, place, start, count in patterns for i in range(count)]
        annotated = annotate_exhibition_series(raw)
        self.assertTrue(all(x["category"] == "ausstellung" for x in annotated))
        self.assertTrue(all(x["exhibitionSeries"] for x in annotated))
        self.assertTrue(all(x["category"] == "sonstiges" for x in raw))  # Rohdaten bleiben
        bars = collapse_adjacent_series(annotated)
        self.assertEqual(len(bars), 4)
        self.assertEqual(sorted(x["seriesCount"] for x in bars), [5, 5, 6, 6])
        self.assertEqual(sum(len(x["seriesDays"]) for x in bars), len(raw))
        self.assertTrue(all(x["allDay"] for x in bars))

    def test_closed_day_breaks_series(self):
        venue = "Stadtmuseum Kaiserslautern"
        raw = [make(date(2026,11,d), "Neues von PFAFF", venue)
               for d in (4,5,6,8,9)]
        result = collapse_adjacent_series(annotate_exhibition_series(raw))
        self.assertEqual(len(result), 2)  # 4–6 und 8–9; geschlossener 7. bleibt frei
        self.assertEqual([(x["start"], x.get("seriesCount")) for x in result],
                         [("2026-11-04", 3), ("2026-11-08", 2)])

    def test_no_inference_without_adjacent_days(self):
        v="Stadtmuseum Kaiserslautern"
        rows=[make(date(2026,11,4), "Neues von PFAFF", v),
              make(date(2026,11,11), "Neues von PFAFF", v)]
        result=annotate_exhibition_series(rows)
        self.assertTrue(all(x["category"]=="sonstiges" for x in result))
        self.assertEqual(collapse_adjacent_series(result),rows)

    def test_excludes_theatre_concerts_and_guides(self):
        v="mpk - Museum Pfalzgalerie Kaiserslautern"
        d=date(2026,11,4)
        rows = [make(d,"Familienführung",v),make(d+timedelta(days=1),"Familienführung",v),
                make(d,"Konzert im Museum",v),make(d+timedelta(days=1),"Konzert im Museum",v),
                make(d,"Hans Purrmann als Sammler","Pfalztheater"),
                make(d+timedelta(days=1),"Hans Purrmann als Sammler","Pfalztheater")]
        self.assertEqual(annotate_exhibition_series(rows),rows)
        self.assertEqual({e['id'] for e in collapse_adjacent_series(rows)}, {e['id'] for e in rows})

    def test_same_day_double_sessions_are_never_merged(self):
        d=date(2026,11,4);v="Stadtmuseum Kaiserslautern"
        rows = [make(d,"Neues von PFAFF",v,id="first"),
                make(d,"Neues von PFAFF",v,id="second",start="2026-11-04T14:00:00+01:00"),
                make(d+timedelta(days=1),"Neues von PFAFF",v)]
        self.assertEqual(annotate_exhibition_series(rows),rows)

    def test_preserves_status_source_and_original_data(self):
        d=date(2026,11,4);v="Stadtmuseum Kaiserslautern"
        rows=[make(d,"Neues von PFAFF",v),
              make(d+timedelta(days=1),"Neues von PFAFF",v, status="tentative"),
              make(d+timedelta(days=2),"Neues von PFAFF",v, sourceKey="rlp")]
        self.assertEqual(annotate_exhibition_series(rows),rows)

    def test_new_labels_excluded_when_already_classified(self):
        d=date(2026,11,4);v="Stadtmuseum Kaiserslautern"
        rows=[make(d,"Museumsführung",v,category="museum"),
              make(d+timedelta(days=1),"Museumsführung",v,category="museum")]
        self.assertEqual(annotate_exhibition_series(rows),rows)

    def test_mixed_events_are_not_reordered(self):
        d=date(2026,11,4);v="Stadtmuseum Kaiserslautern"
        series=[make(d,"Neues von PFAFF",v),
                make(d+timedelta(days=1),"Neues von PFAFF",v)]
        unrelated=make(d,"Familienführung",v)
        events=[unrelated,series[1],series[0]]
        out=annotate_exhibition_series(events)
        self.assertEqual([e["id"] for e in out],[e["id"] for e in events])
        self.assertEqual(out[0]["category"],"sonstiges")
        self.assertEqual([e["category"] for e in out[1:]],["ausstellung","ausstellung"])


if __name__=="__main__":
    unittest.main()
