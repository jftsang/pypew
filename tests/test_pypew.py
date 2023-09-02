import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlencode

from dateutil.utils import today
from flask import url_for
from parameterized import parameterized

import views
from filters import english_date
from models import Feast, Music, Service
from models_base import get
from pypew import create_app, PyPew
from utils import advent


def m_create_docx_impl(path):
    Path(path).touch()


class TestDates(unittest.TestCase):
    @parameterized.expand([
        # Christmas Day in 2021 was a Saturday
        (2021, date(2021, 11, 28)),
        # Sunday (special case!)
        (2022, date(2022, 11, 27)),
        # Monday
        (2023, date(2023, 12, 3)),
    ])
    def test_advent(self, year, expected_date):
        self.assertEqual(advent(year), expected_date)

    @parameterized.expand([
        ('Advent I', 2022, date(2022, 11, 27)),  # coadvent
        ('Christmas Day', 2022, date(2022, 12, 25)),  # fixed
        ('Easter Day', 2022, date(2022, 4, 17)),  # coeaster
        ('Trinity Sunday', 2022, date(2022, 6, 12)),  # coeaster
        ('Remembrance Sunday', 2022, date(2022, 11, 13)),  # closest Sunday
        ('Remembrance Sunday', 2024, date(2024, 11, 10)),  # closest Sunday
    ])
    def test_get_date(self, name, year, expected_date):
        self.assertEqual(Feast.get(name=name).get_date(year), expected_date)

    @parameterized.expand([
        (date(2023, 9, 1), "Friday 1st September 2023"),
        (date(2023, 9, 2), "Saturday 2nd September 2023"),
        (date(2023, 9, 3), "Sunday 3rd September 2023"),
        (date(2023, 9, 4), "Monday 4th September 2023"),
        (date(2023, 9, 11), "Monday 11th September 2023"),
        (date(2023, 9, 12), "Tuesday 12th September 2023"),
        (date(2023, 9, 13), "Wednesday 13th September 2023"),
        (date(2023, 9, 14), "Thursday 14th September 2023"),
        (date(2023, 9, 21), "Thursday 21st September 2023"),
        (date(2023, 9, 22), "Friday 22nd September 2023"),
        (date(2023, 9, 23), "Saturday 23rd September 2023"),
        (date(2023, 9, 24), "Sunday 24th September 2023"),
    ])
    def test_english_ordinals(self, supplied_date, expected_string):
        self.assertEqual(english_date(supplied_date), expected_string)


class TestModels(unittest.TestCase):
    def test_neh_lookup(self):
        music = Music.get_neh_hymn_by_ref('NEH: 1a')
        self.assertEqual(
            music,
            Music(title='Creator of the stars of night',
                  category='Hymn',
                  composer=None,
                  lyrics=None,
                  ref='NEH: 1a')
        )

    def test_neh_lookup_unsuccessful(self):
        music = Music.get_neh_hymn_by_ref('NEHHH: 10000k')
        self.assertIsNone(music)

    def test_collects_normal(self):
        primary = get(Feast.all(), name='Septuagesima')
        service = Service(title='', date=today(), primary_feast=primary)
        self.assertListEqual(service.collects, [primary.collect])

    def test_collects_with_secondary_feast(self):
        primary = get(Feast.all(), name='Septuagesima')
        secondary = get(Feast.all(), name='Christmas Day')
        service = Service(title='', date=today(), primary_feast=primary, secondary_feast=secondary)
        self.assertListEqual(service.collects, [primary.collect, secondary.collect])

    def test_collect_on_advent1(self):
        advent1 = get(Feast.all(), name='Advent I')
        service = Service(title='', date=today(), primary_feast=advent1)
        self.assertListEqual(service.collects, [advent1.collect])

    def test_collects_during_advent(self):
        advent1 = get(Feast.all(), name='Advent I')
        advent2 = get(Feast.all(), name='Advent II')
        service = Service(title='', date=today(), primary_feast=advent2)
        self.assertListEqual(service.collects, [advent2.collect, advent1.collect])

    def test_collects_during_lent(self):
        ash_wednesday = get(Feast.all(), name='Ash Wednesday')
        lent1 = get(Feast.all(), name='Lent I')
        service = Service(title='', date=today(), primary_feast=lent1)
        self.assertListEqual(service.collects, [lent1.collect, ash_wednesday.collect])


class TestViews(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app(PyPew())
        self.app.config['SERVER_NAME'] = 'localhost:5000'
        self.app.app_context().push()
        self.client = self.app.test_client()

    def test_all_views_registered(self):
        """All the views in the 'views' module (and its imports) should
        be registered.
        """
        for x in dir(views):
            if (x.endswith('_view') or x.endswith('_api')):
                self.assertIn(x, self.app.view_functions)

    def test_index_view(self):
        r = self.client.get(url_for('index_view'))
        self.assertEqual(r.status_code, 200)

    def test_acknowledgements_view(self):
        r = self.client.get(url_for('acknowledgements_view'))
        self.assertEqual(r.status_code, 200)

    def test_feast_index_view(self):
        r = self.client.get(url_for('feast_index_view'))
        self.assertEqual(r.status_code, 200)

    @parameterized.expand([
        (feast.slug,) for feast in Feast.all()
    ])
    def test_can_load_all_feasts(self, slug):
        endpoint = url_for('feast_detail_view', slug=slug)
        r = self.client.get(endpoint)
        self.assertEqual(200, r.status_code, msg=f"Couldn't load {endpoint}")

    @parameterized.expand([
        (feast.slug,) for feast in Feast.all()
    ])
    def test_feast_api(self, slug):
        endpoint = url_for('feast_detail_api', slug=slug)
        r = self.client.get(endpoint)
        self.assertEqual(200, r.status_code, msg=f"Couldn't load {endpoint}")
        self.assertTrue(r.is_json)

    @parameterized.expand([
        (feast.slug,) for feast in Feast.all()
    ])
    def test_feast_date_api(self, slug):
        endpoint = url_for('feast_date_api', slug=slug)
        r = self.client.get(endpoint)
        self.assertEqual(200, r.status_code, msg=f"Couldn't load {endpoint}")

    def test_feast_detail_view_handles_not_found(self):
        r = self.client.get(
            url_for('feast_detail_view', slug='notmas-day')
        )
        self.assertEqual(r.status_code, 404)

    @patch('pypew.views.feast_views.Feast.create_docx', side_effect=m_create_docx_impl)
    def test_feast_docx_view(self, m_create_docx):
        r = self.client.get(
            url_for('feast_docx_view', slug='christmas-day')
        )
        m_create_docx.assert_called()
        self.assertEqual(200, r.status_code)
        self.assertEqual(
            'attachment; filename="Christmas Day.docx"',
            r.headers['Content-Disposition'],
        )
        self.assertEqual(
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            r.headers['Content-Type'],
        )

    @patch('pypew.views.pew_sheet_views.Service.create_docx', side_effect=m_create_docx_impl)
    def test_pew_sheet_docx_view(self, m_create_docx):
        r = self.client.get(
            url_for('pew_sheet_docx_view') + '?' + urlencode(
                {'title': 'Feast of Foo', 'date': '2022-01-01',
                 'primary_feast_name': 'advent-i',
                 'secondary_feast_name': '', 'introit_hymn': '',
                 'offertory_hymn': '', 'recessional_hymn': ''})
        )
        self.assertEqual(r.status_code, 200)
        m_create_docx.assert_called()
        self.assertEqual(
            r.headers['Content-Disposition'],
            'attachment; filename="2022-01-01 Feast of Foo.docx"'
        )
        self.assertEqual(
            r.headers['Content-Type'],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )


if __name__ == '__main__':
    unittest.main()
