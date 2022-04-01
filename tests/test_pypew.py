import unittest
from datetime import date
from unittest.mock import patch
from urllib.parse import urlencode

from dateutil.utils import today
from flask import url_for
from parameterized import parameterized

from models import Feast, Music, Service, get
from utils import advent
from ..pypew import create_app


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
        self.app = create_app()
        self.app.config['SERVER_NAME'] = 'localhost:5000'
        self.app.app_context().push()
        self.client = self.app.test_client()

    def test_index_view(self):
        r = self.client.get(url_for('index_view'))
        self.assertEqual(r.status_code, 200)

    def test_acknowledgements_view(self):
        r = self.client.get(url_for('acknowledgements_view'))
        self.assertEqual(r.status_code, 200)

    def test_feast_index_view(self):
        r = self.client.get(url_for('feast_index_view'))
        self.assertEqual(r.status_code, 200)

    def test_feast_detail_view(self):
        r = self.client.get(
            url_for('feast_detail_view', name='Christmas Day')
        )
        self.assertEqual(r.status_code, 200)

    def test_feast_detail_view_handles_not_found(self):
        r = self.client.get(
            url_for('feast_detail_view', name='Notmas Day')
        )
        self.assertEqual(r.status_code, 404)

    @patch('pypew.views.feast_views.Feast.create_docx')
    def test_feast_docx_view(self, m_create_docx):
        r = self.client.get(
            url_for('feast_docx_view', name='Christmas Day')
        )
        m_create_docx.assert_called()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r.headers['Content-Disposition'],
            'attachment; filename="Christmas Day.docx"'
        )
        self.assertEqual(
            r.headers['Content-Type'],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

    @unittest.expectedFailure
    @patch('pypew.views.convert')
    @patch('pypew.views.Feast.create_docx')
    def test_feast_pdf_view(self, m_create_docx, m_convert):
        r = self.client.get(
            url_for('feast_pdf_view', name='Christmas Day')
        )
        m_convert.assert_called()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers['Content-Disposition'],
                         'attachment; filename="Christmas Day.pdf"')

    @patch('pypew.views.pew_sheet_views.Service.create_docx')
    def test_pew_sheet_docx_view(self, m_create_docx):
        r = self.client.get(
            url_for('pew_sheet_docx_view') + '?' + urlencode(
                {'title': 'Feast of Foo', 'date': '2022-01-01', 'primary_feast_name': 'Advent I',
                 'secondary_feast_name': '', 'introit_hymn': '', 'offertory_hymn': '', 'recessional_hymn': ''})
        )
        m_create_docx.assert_called()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r.headers['Content-Disposition'],
            'attachment; filename="Feast of Foo.docx"'
        )
        self.assertEqual(
            r.headers['Content-Type'],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )


if __name__ == '__main__':
    unittest.main()
