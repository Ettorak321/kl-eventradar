import unittest
from datetime import date
from scripts.special_days import easter_sunday, annual_days, attach_calendar_days


class TestCalendarDays(unittest.TestCase):
    def test_easter(self):
        self.assertEqual(easter_sunday(2026), date(2026, 4, 5))
        self.assertEqual(easter_sunday(2027), date(2027, 3, 28))
        self.assertEqual(easter_sunday(2038), date(2038, 4, 25))

    def test_all_eleven_legal_holidays_in_rhineland_palatinate(self):
        events = annual_days(2027)
        legal = {e["title"]: e["start"] for e in events if e["isPublicHoliday"]}
        self.assertEqual(len(legal), 11)
        self.assertEqual(legal["Karfreitag"], "2027-03-26")
        self.assertEqual(legal["Ostermontag"], "2027-03-29")
        self.assertEqual(legal["Christi Himmelfahrt (Vatertag)"], "2027-05-06")
        self.assertEqual(legal["Pfingstmontag"], "2027-05-17")
        self.assertEqual(legal["Fronleichnam"], "2027-05-27")
        self.assertEqual(legal["Allerheiligen"], "2027-11-01")

    def test_special_occasions_are_not_legal_holidays(self):
        events = {e["title"]: e for e in annual_days(2027)}
        for name, when in [("St. Patrick's Day", "2027-03-17"), ("Halloween", "2027-10-31"),
                           ("Silvester", "2027-12-31"), ("Rosenmontag", "2027-02-08"),
                           ("Weiberfastnacht", "2027-02-04"), ("Muttertag", "2027-05-09"),
                           ("Black Friday", "2027-11-26"), ("1. Advent", "2027-11-28"),
                           ("4. Advent", "2027-12-19")]:
            self.assertEqual(events[name]["start"], when)
            self.assertEqual(events[name]["category"], "anlass")
            self.assertFalse(events[name]["isPublicHoliday"])
            self.assertFalse(events[name]["isMajor"])
        self.assertEqual(events["Silvester"]["end"], "2028-01-01")

    def test_new_years_and_no_double_insertion(self):
        original = [{"id": "fck-1", "title": "FCK-Test", "start": "2026-11-01", "region": "stadt-kl"}]
        events = attach_calendar_days(original, today=date(2026, 10, 28))
        self.assertEqual(len(events), 1 + 6 * 32)
        self.assertEqual({e["start"][:4] for e in events if e.get("isAnnualDay")}, {
            "2026", "2027", "2028", "2029", "2030", "2031"})
        rerun = attach_calendar_days(events, today=date(2026, 10, 28))
        self.assertEqual([e["id"] for e in events if e.get("id")], [e["id"] for e in rerun if e.get("id")])
        self.assertEqual(len({e["id"] for e in events if e.get("isAnnualDay")}), 6 * 32)

    def test_region_is_global_but_not_real_venue(self):
        e = annual_days(2027)[0]
        self.assertEqual(e["region"], "alle-regionen")
        self.assertFalse(e["isStadium"])
        self.assertTrue(e["allDay"])
        self.assertEqual(e["status"], "calendar")


if __name__ == "__main__":
    unittest.main()
