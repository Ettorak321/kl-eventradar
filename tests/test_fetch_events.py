import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts import fetch_events as fe

FIXTURES = Path(__file__).parent / 'fixtures'

def fixture(name):
    return (FIXTURES / name).read_text(encoding='utf-8')

def item(source, ident, title='Ein Termin'):
    return {'id': f'{source}-{ident}', 'sourceKey': source, 'title': title, 'start': '2026-11-02',
            'end': None, 'allDay': True, 'location': 'Kaiserslautern', 'category': 'kultur'}

class TestFCK(unittest.TestCase):
    def test_heimspiel(self):
        self.assertTrue(fe.is_home_game('1. FC Kaiserslautern - Schalke 04', 'Fritz-Walter-Stadion, Kaiserslautern'))
    def test_auswaerts_nicht_heim(self):
        self.assertFalse(fe.is_home_game('Hannover 96 - 1. FC Kaiserslautern', 'Heinz von Heiden Arena, Hannover'))
    def test_ort_unbekannt_nicht_heim(self):
        self.assertFalse(fe.is_home_game('1. FC Kaiserslautern - Bochum', ''))
    def test_away_even_with_inconsistent_venue(self):
        self.assertFalse(fe.is_home_game('Hannover 96 - 1. FC Kaiserslautern','Fritz-Walter-Stadion'))
    def test_anderes_stadion_in_kaiserslautern(self):
        self.assertFalse(fe.is_home_game('1. FC Kaiserslautern - Bochum', 'Andere Sportanlage, Kaiserslautern'))
    def test_nachwuchs_keine_stadionbelegung(self):
        self.assertFalse(fe.is_home_game('FCK-U21 - Freiburg II', 'Fritz-Walter-Stadion'))
    def test_mixed_feed_excludes_away_unknown_and_training(self):
        with patch.object(fe,'fetch',return_value=SimpleNamespace(content=(FIXTURES/'fck_mixed.ics').read_bytes())):
            events=fe.parse_fck_ics('https://feed.example/ics')
        self.assertEqual(len(events),2)
        events=[ev for ev in events if ev['isStadium']]
        self.assertEqual(events[0]['category'],'fussball')
        self.assertTrue(events[0]['venueVerified'])
        self.assertTrue(events[0]['isStadium'])
        self.assertEqual(events[0]['start'],'2026-11-08T13:30:00+01:00')
    def test_floating_and_utc_dates(self):
        a,ad=fe.parse_ics_date(('DTSTART','20261017T133000'))
        b,bd=fe.parse_ics_date(('DTSTART','20260717T113000Z'))
        self.assertFalse(ad or bd)
        self.assertEqual(a,'2026-10-17T13:30:00+02:00')
        self.assertEqual(b,'2026-07-17T13:30:00+02:00')
    def test_home_source_uid_is_stable(self):
        with patch.object(fe,'fetch',return_value=SimpleNamespace(content=(FIXTURES/'home_game.ics').read_bytes())):
            first=fe.parse_fck_ics('x')[0]
            second=fe.parse_fck_ics('x')[0]
        self.assertEqual(first['id'],second['id'])

class TestCity(unittest.TestCase):
    def test_parsed_page_excludes_kusel_and_no_invented_time(self):
        results=fe.extract_city_page(fixture('city_page_1.html'))
        self.assertEqual(len(results),1)
        self.assertEqual(results[0]['title'],'Oktoberkerwe')
        self.assertEqual(results[0]['start'],'2026-10-22')
        self.assertTrue(results[0]['allDay'])
    def test_pagination(self):
        def get(url,session=None,timeout=22):
            name='city_page_2.html' if '?page=2' in url else 'city_page_1.html'
            return SimpleNamespace(text=fixture(name))
        with patch.object(fe,'fetch',side_effect=get),patch.object(fe.time,'sleep'):
            events=fe.fetch_city()
        self.assertEqual(len(events),2)
    def test_pagination_incomplete_is_error(self):
        with patch.object(fe,'fetch',return_value=SimpleNamespace(text=fixture('city_page_1.html'))),patch.object(fe.time,'sleep'):
            with self.assertRaises(fe.SourceError):fe.fetch_city()
    def test_city_multiday_dates(self):
        result=fe.parse_german_schedule('09. Juni - 15. September 2026')
        self.assertEqual(result,('2026-06-09','2026-09-16',True))
    def test_geofence(self):
        self.assertFalse(fe.in_city('Kulturzentrum Kinett Kusel'))
        self.assertFalse(fe.in_city('Marktplatz Steinwenden'))
        self.assertTrue(fe.in_city('Fruchthalle'))

class TestSommerswing(unittest.TestCase):
    def test_explicit_program(self):
        events=fe.parse_sommerswing_html(fixture('sommerswing.html'))
        self.assertEqual(len(events),2)
        self.assertIn('Suzi Brown',events[0]['title'])
        self.assertEqual(events[1]['start'],'2026-08-05T19:00:00+02:00')
    def test_no_year_not_guessed(self):
        with self.assertRaises(fe.SourceError):fe.parse_sommerswing_html('<h3>Band</h3><h2>8. Juli</h2>')

class TestCache(unittest.TestCase):
    def test_failed_fck_preserved_when_city_succeeds(self):
        with tempfile.TemporaryDirectory() as root:
            cache=Path(root)/'cache';data=Path(root)/'data'
            first=fe.update_sources({'fck': lambda:[item('fck','1','FCK - Bochum')], 'city':lambda:[item('city','1','Altstadtfest')]},cache,data)
            self.assertEqual(len([e for e in first['events'] if not e.get('isAnnualDay')]),2)
            def fail():raise fe.SourceError('FCK nicht erreichbar')
            second=fe.update_sources({'fck':fail,'city':lambda:[item('city','2','Oktoberkerwe')]},cache,data)
            self.assertEqual({x['id'] for x in second['events'] if not x.get('isAnnualDay')},{'fck-1','city-2'})
            self.assertTrue(next(x for x in second['events'] if x['sourceKey']=='fck')['stale'])
            self.assertEqual(second['sourceStatus']['fck']['status'],'error')
            self.assertEqual(second['sourceStatus']['city']['status'],'ok')
            self.assertEqual(fe.read_json(cache/'fck.json',{})['events'][0]['id'],'fck-1')
    def test_all_fail_do_not_fake_success(self):
        with tempfile.TemporaryDirectory() as root:
            cache=Path(root)/'cache';data=Path(root)/'data'
            fe.update_sources({'fck':lambda:[item('fck','1')]},cache,data)
            before=fe.read_json(data/'events.json',{})['lastSuccessfulSync']
            def fail():raise fe.SourceError('offline')
            result=fe.update_sources({'fck':fail},cache,data)
            self.assertEqual(result['lastSuccessfulSync'],before)
            self.assertEqual(result['sourceStatus']['fck']['status'],'error')
    def test_never_invent_ids_or_duplicate_city_sommerswing(self):
        swing=item('sommerswing','1','Sommerswing: Band');swing['start']='2026-11-02T19:00:00+01:00'
        city=item('city','1','Sommerswing im Volkspark');city['start']='2026-11-02'
        out=fe.dedupe_cross_sources([city,swing])
        self.assertEqual([e['sourceKey'] for e in out],['sommerswing'])

if __name__=='__main__':unittest.main()
