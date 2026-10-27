import unittest
from scripts.event_taxonomy import classify_event, relabel
from scripts.regions import classify_region
from scripts import fetch_events as fe
from scripts import regional_sources as rs


class TaxonomyV5Tests(unittest.TestCase):
    def test_independent_categories(self):
        cases={
            'Kerwe in Weilerbach':'kerwe',
            'Altstadtfest Kaiserslautern':'stadtfest',
            'Konzert im Volkspark':'konzert',
            'Fußballturnier Rodenbach':'sport',
            'Flohmarkt am Rathaus':'markt',
            'Ausstellung im Museum':'ausstellung',
            'Museumsführung Kaiserslautern':'museum',
            'Theateraufführung':'kultur',
            'Vereinstreffen':'sonstiges',
        }
        for title, expected in cases.items():
            with self.subTest(title=title):
                self.assertEqual(classify_event(title), expected)

    def test_fck_requires_verified_stadium_and_feed(self):
        verified={'sourceKey':'fck','isStadium':True,'venueVerified':True,
                  'title':'1. FC Kaiserslautern – Hertha BSC','region':'stadt-kl'}
        self.assertEqual(relabel(verified)['category'],'fussball')
        for changes in ({'isStadium':False},{'venueVerified':False},{'sourceKey':'city'}):
            self.assertNotEqual(relabel({**verified,**changes})['category'],'fussball')

    def test_old_cache_migrates_kerwe_without_stadium(self):
        original={'sourceKey':'weilerbach','category':'stadtfest','eventType':'Fest',
                  'title':'Kerwe in Weilerbach','isStadium':False}
        updated=relabel(original)
        self.assertEqual(updated['category'],'kerwe')
        self.assertEqual(updated['eventType'],'Kerwe')
        self.assertFalse(updated['isStadium'])
        self.assertEqual(original['category'],'stadtfest')

    def test_ambiguous_linden_name_does_not_prove_vg_linden(self):
        self.assertEqual(classify_region('Platz unter den Linden'),(None,None))
        self.assertEqual(classify_region('Kerwe in Linden')[0],'vg-landstuhl')

    def test_theater_trip_to_kl_not_event_in_kl(self):
        self.assertFalse(fe.in_city('Abfahrt Waldmohr Mitte zum Pfalztheater Kaiserslautern'))
        rows=[{'id':'trip','name':'Theaterfahrten',
               'location':'Abfahrt Waldmohr Mitte zum Pfalztheater Kaiserslautern',
               'startDate':'2026-11-02'}]
        out=rs.parse_rlp_json(rows,fe.TZ,fe.stable_id,fe.stamp,fe.category,fe.status_from)
        self.assertEqual(out,[])


if __name__=='__main__':unittest.main()
