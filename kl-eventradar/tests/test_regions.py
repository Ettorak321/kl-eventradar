import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo
from scripts import fetch_events as fe
from scripts import regional_sources as rs
from scripts.regions import REGIONS, classify_region

FIXTURES = Path(__file__).parent/'fixtures'

class RegionMappingTests(unittest.TestCase):
    def test_all_six_district_areas_plus_city(self):
        self.assertEqual(len(REGIONS),7)
        examples={'stadt-kl':'Kaiserslautern', 'vg-bruchmuehlbach':'Bruchmühlbach-Miesau',
            'vg-enkenbach':'Enkenbach-Alsenborn','vg-landstuhl':'Landstuhl',
            'vg-otterbach':'Otterbach','vg-ramstein':'Ramstein-Miesenbach','vg-weilerbach':'Weilerbach'}
        for region,place in examples.items():
            with self.subTest(region=region):self.assertEqual(classify_region(place)[0],region)
    def test_ortsteile_not_only_vg_seats(self):
        cases={'Hütschenhausen':'vg-ramstein','Rodenbach':'vg-weilerbach','Schwedelbach':'vg-weilerbach',
            'Trippstadt':'vg-landstuhl','Frankenstein':'vg-enkenbach','Niederkirchen':'vg-otterbach',
            'Gerhardsbrunn':'vg-bruchmuehlbach','Stiftskirche Kaiserslautern':'stadt-kl'}
        for name,expected in cases.items():
            with self.subTest(place=name):self.assertEqual(classify_region(name)[0],expected)
    def test_other_kreise_and_unknown_not_included(self):
        for text in ('Kusel','Homburg','Unbekannter Ort','Landkreis Kaiserslautern'):
            with self.subTest(place=text):self.assertIsNone(classify_region(text)[0])
    def test_village_wins_over_mention_of_city(self):
        self.assertEqual(classify_region('Stadthalle Landstuhl, Kreis Kaiserslautern')[0], 'vg-landstuhl')

class RegionalSourceTests(unittest.TestCase):
    @staticmethod
    def parse(payload):
        return rs.parse_rlp_json(payload,fe.TZ,fe.stable_id,fe.stamp,fe.category,fe.status_from)
    def test_rlp_filters_kusel_and_unknown(self):
        events=self.parse(json.loads((FIXTURES/'rlp_region_events.json').read_text()))
        self.assertEqual(len(events),7)
        self.assertEqual({x['region'] for x in events},set(REGIONS))
        self.assertTrue(next(x for x in events if 'Rodenbach' in x['title'])['allDay'])
        self.assertEqual(next(x for x in events if 'Rodenbach' in x['title'])['eventType'],'Kerwe')
        self.assertEqual(next(x for x in events if 'Rodenbach' in x['title'])['end'],'2026-11-09')
        self.assertEqual(next(x for x in events if 'Landstuhl' in x['title'])['start'],'2026-11-14T20:00:00+01:00')
    def test_invalid_rlp_schema_raises(self):
        with self.assertRaises(ValueError):self.parse({'unrelated':{}})
    def test_ramstein_html_extracts_known_venues_only(self):
        events=rs.parse_ramstein_html((FIXTURES/'ramstein_calendar.html').read_text(),fe.TZ,fe.stable_id,fe.stamp,fe.category,fe.status_from)
        self.assertEqual(len(events),4)
        self.assertEqual(events[0]['region'],'vg-ramstein')
        self.assertEqual(events[0]['start'],'2026-10-16')
        self.assertEqual(events[0]['end'],'2026-10-21')
        self.assertEqual(events[0]['eventType'],'Kerwe')
        self.assertEqual(events[1]['start'],'2026-10-23T19:30:00+02:00')
    def test_weilerbach_article_date_ranges(self):
        events=rs.parse_weilerbach_article((FIXTURES/'wittich_weilerbach.html').read_text(),
            'https://ol.wittich.de/titel/798/ausgabe/36/2026/artikel/123',fe.TZ,fe.stable_id,fe.stamp,fe.category,fe.status_from)
        self.assertEqual(len(events),2)
        self.assertEqual(events[0]['start'],'2026-09-25')
        self.assertEqual(events[0]['end'],'2026-09-29')
        self.assertEqual(events[0]['region'],'vg-weilerbach')
    def test_wittich_discovery_is_explicit(self):
        raw='<a href="/titel/798/ausgabe/36/2026/artikel/123">Veranstaltungskalender Verbandsgemeinde Weilerbach</a>'
        self.assertEqual(rs.weilerbach_article_links(raw,'https://ol.wittich.de/titel/798'),
            ['https://ol.wittich.de/titel/798/ausgabe/36/2026/artikel/123'])
    def test_source_cache_isolated_across_six_new_sources(self):
        def ev(key,region):return {'id':f'{key}-1','sourceKey':key,'title':'Fest','start':'2026-10-25','location':REGIONS[region]['name'],'region':region}
        with tempfile.TemporaryDirectory() as td:
            td=Path(td)
            fe.update_sources({'rlp':lambda:[ev('rlp','vg-landstuhl')], 'ramstein':lambda:[ev('ramstein','vg-ramstein')]},td/'cache',td/'data')
            def fail():raise fe.SourceError('offline')
            result=fe.update_sources({'rlp':fail,'ramstein':lambda:[ev('ramstein','vg-ramstein')]},td/'cache',td/'data')
            self.assertTrue(next(x for x in result['events'] if x['sourceKey']=='rlp')['stale'])
            self.assertEqual(result['sourceStatus']['rlp']['status'],'error')
            self.assertEqual(result['sourceStatus']['ramstein']['status'],'ok')

if __name__=='__main__':unittest.main()
