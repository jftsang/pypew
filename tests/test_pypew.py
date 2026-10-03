import json
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlencode

from dateutil.utils import today
from flask import url_for
from parameterized import parameterized
from pydantic import ValidationError

from pypew import views
from pypew.app import create_app
from pypew.filters import english_date
from pypew.models import Feast, Music, Service
from pypew.models_base import get

# The date each feast falls on, as an ISO string or null, keyed by slug and
# then year. This pins the date expressions in the feast files, so changing
# one on purpose means regenerating this file -- and that regeneration shows
# up in the diff as the dates that moved. Regenerate with:
#
#   uv run python -c 'import json; from pypew.models import Feast; \
#     g = {f.slug: {str(y): (d.isoformat() if (d := f.get_date(y)) else None) \
#       for y in range(2022, 2033)} for f in Feast.all()}; \
#     open("tests/feast_dates.json", "w").write(json.dumps(g, indent=2) + "\n")'
GOLDEN_DATES = json.loads((Path(__file__).parent / "feast_dates.json").read_text())


def m_create_docx_impl(path):
    Path(path).touch()


class TestDates(unittest.TestCase):
    @parameterized.expand(
        [
            ("Advent I", 2022, date(2022, 11, 27)),  # Advent Sunday
            ("Christmas Day", 2022, date(2022, 12, 25)),  # fixed date
            ("Easter Day", 2022, date(2022, 4, 17)),  # Easter
            ("Trinity Sunday", 2022, date(2022, 6, 12)),  # a week after Whit Sunday
            ("Remembrance Sunday", 2022, date(2022, 11, 13)),  # nearest Sunday
            ("Remembrance Sunday", 2024, date(2024, 11, 10)),  # nearest Sunday
        ]
    )
    def test_get_date(self, name, year, expected_date):
        self.assertEqual(Feast.get(name=name).get_date(year), expected_date)

    def test_golden_dates(self):
        """Every feast falls where the golden file says it does.

        The feasts with no date of their own are recorded as null rather than
        omitted, so one cannot quietly acquire a date expression either.
        """
        for slug, years in GOLDEN_DATES.items():
            feast = Feast.from_yaml(slug)
            for year, expected in years.items():
                with self.subTest(slug=slug, year=year):
                    actual = feast.get_date(int(year))
                    assert (
                        actual is None and expected is None
                    ) or actual == date.fromisoformat(expected)

    def test_golden_dates_cover_every_feast(self):
        """A new feast file fails here until the golden file is regenerated."""
        self.assertEqual(set(GOLDEN_DATES), {f.slug for f in Feast.all()})

    @parameterized.expand(
        [
            ("Easter",),
            ("8 weeks after Easter",),
            ("Remembrance Sunday",),
            ("25 December",),
            (None,),
        ]
    )
    def test_valid_dateexpr_is_accepted(self, dateexpr):
        Feast(slug="x", name="X", dateexpr=dateexpr)

    @parameterized.expand(
        [
            ("banana",),
            ("8 fortnights after Easter",),
            ("Someday",),
            ("25 December and also Easter",),
        ]
    )
    def test_invalid_dateexpr_is_rejected(self, dateexpr):
        """A typo in a feast file is reported when the file loads."""
        with self.assertRaises(ValidationError) as cm:
            Feast(slug="x", name="X", dateexpr=dateexpr)
        self.assertIn(repr(dateexpr), str(cm.exception))

    @parameterized.expand(
        [
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
        ]
    )
    def test_english_ordinals(self, supplied_date, expected_string):
        self.assertEqual(english_date(supplied_date), expected_string)


try:
    import pandas as pd
except ImportError:
    pd = None


@unittest.skipIf(pd is None, "Pandas not available")
class TestModels(unittest.TestCase):
    def test_neh_lookup(self):
        music = Music.get_neh_hymn_by_ref("NEH: 1a")
        self.assertEqual(
            music,
            Music(
                title="Creator of the stars of night",
                category="Hymn",
                composer=None,
                lyrics=None,
                ref="NEH: 1a",
                # FIXME(E501): long literal, not splittable by the formatter
                translation="Words/translation available at NEH: 1a, Creator of the stars of night",
            ),
        )

    def test_neh_lookup_unsuccessful(self):
        music = Music.get_neh_hymn_by_ref("NEHHH: 10000k")
        self.assertIsNone(music)

    def test_collects_normal(self):
        primary = get(Feast.all(), name="Septuagesima")
        service = Service(title="", date=today(), primary_feast=primary)
        self.assertListEqual(service.collects, [primary.collect])

    def test_collects_with_secondary_feast(self):
        primary = get(Feast.all(), name="Septuagesima")
        secondary = get(Feast.all(), name="Christmas Day")
        service = Service(
            title="", date=today(), primary_feast=primary, secondary_feasts=[secondary]
        )
        self.assertListEqual(service.collects, [primary.collect, secondary.collect])

    def test_collects_with_two_secondary_feasts(self):
        primary = get(Feast.all(), name="Septuagesima")
        secondary1 = get(Feast.all(), name="Christmas Day")
        secondary2 = get(Feast.all(), name="St. Stephen")
        service = Service(
            title="",
            date=today(),
            primary_feast=primary,
            secondary_feasts=[secondary1, secondary2],
        )
        self.assertListEqual(
            service.collects, [primary.collect, secondary1.collect, secondary2.collect]
        )

    def test_collect_on_advent1(self):
        advent1 = get(Feast.all(), name="Advent I")
        service = Service(title="", date=today(), primary_feast=advent1)
        self.assertListEqual(service.collects, [advent1.collect])

    def test_collects_during_advent(self):
        advent1 = get(Feast.all(), name="Advent I")
        advent2 = get(Feast.all(), name="Advent II")
        service = Service(title="", date=today(), primary_feast=advent2)
        self.assertListEqual(service.collects, [advent2.collect, advent1.collect])

    def test_collects_during_lent(self):
        ash_wednesday = get(Feast.all(), name="Ash Wednesday")
        lent1 = get(Feast.all(), name="Lent I")
        service = Service(title="", date=today(), primary_feast=lent1)
        self.assertListEqual(service.collects, [lent1.collect, ash_wednesday.collect])


class TestViews(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app()
        self.app.config["SERVER_NAME"] = "localhost:5000"
        self.app.app_context().push()
        self.client = self.app.test_client()

    def test_all_views_registered(self):
        """All the views in the 'views' module (and its imports) should
        be registered.
        """
        for x in dir(views):
            # FIXME(PIE810): explicit .endswith chain
            if x.endswith("_view") or x.endswith("_api"):
                self.assertIn(x, self.app.view_functions)

    def test_index_view(self):
        r = self.client.get(url_for("index_view"))
        self.assertEqual(r.status_code, 200)

    def test_acknowledgements_view(self):
        r = self.client.get(url_for("acknowledgements_view"))
        self.assertEqual(r.status_code, 200)

    def test_feast_index_view(self):
        r = self.client.get(url_for("feast_index_view"))
        self.assertEqual(r.status_code, 200)

    @parameterized.expand([(feast.slug,) for feast in Feast.all()])
    def test_can_load_all_feasts(self, slug):
        endpoint = url_for("feast_detail_view", slug=slug)
        r = self.client.get(endpoint)
        self.assertEqual(200, r.status_code, msg=f"Couldn't load {endpoint}")

    @parameterized.expand([(feast.slug,) for feast in Feast.all()])
    def test_feast_api(self, slug):
        endpoint = url_for("feast_detail_api", slug=slug)
        r = self.client.get(endpoint)
        self.assertEqual(200, r.status_code, msg=f"Couldn't load {endpoint}")
        self.assertTrue(r.is_json)

    @parameterized.expand([(feast.slug,) for feast in Feast.all()])
    def test_feast_date_api(self, slug):
        endpoint = url_for("feast_date_api", slug=slug)
        r = self.client.get(endpoint)
        self.assertEqual(200, r.status_code, msg=f"Couldn't load {endpoint}")

    def test_feast_index_api(self):
        r = self.client.get(url_for("feast_index_api"))
        self.assertEqual(200, r.status_code)
        self.assertTrue(r.is_json)

        feasts = r.get_json()
        self.assertEqual(len(feasts), len(Feast.all()))
        self.assertEqual(
            set(feasts[0]),
            set(Feast.model_fields),
            msg="every field should be serialized",
        )
        self.assertEqual(feasts[0]["slug"], Feast.all()[0].slug)

    def test_feast_detail_api_serializes_every_field(self):
        r = self.client.get(url_for("feast_detail_api", slug="christmas-day"))
        self.assertEqual(200, r.status_code)
        self.assertTrue(r.is_json)

        feast = r.get_json()
        self.assertEqual(set(feast), set(Feast.model_fields))
        self.assertEqual(feast["name"], "Christmas Day")

    @parameterized.expand(
        [
            ("2022", "2022-11-27"),
            ("2024", "2024-12-01"),
        ]
    )
    def test_feast_date_api_with_year(self, year, expected_date):
        r = self.client.get(
            url_for("feast_date_api", slug="advent-i") + f"?year={year}"
        )
        self.assertEqual(200, r.status_code)
        self.assertEqual(r.get_json(), expected_date)

    def test_feast_date_api_with_bad_year(self):
        r = self.client.get(
            url_for("feast_date_api", slug="advent-i") + "?year=not-a-year"
        )
        self.assertEqual(400, r.status_code)

    def test_feast_date_api_handles_not_found(self):
        r = self.client.get(url_for("feast_date_api", slug="notmas-day"))
        self.assertEqual(404, r.status_code)

    def test_feast_upcoming_api(self):
        r = self.client.get(url_for("feast_upcoming_api") + "?date=2022-01-01")
        self.assertEqual(200, r.status_code)
        self.assertTrue(r.is_json)

        upcoming = r.get_json()
        self.assertEqual(len(upcoming), len(Feast.all()))
        self.assertEqual(
            [f["index"] for f in upcoming],
            list(range(len(upcoming))),
            msg="the soonest feast comes first",
        )
        self.assertEqual(upcoming[0]["slug"], "the-naming-circumcision-of-christ")
        self.assertEqual(upcoming[0]["name"], "The Naming & Circumcision of Christ")
        self.assertEqual(upcoming[0]["next"], "Saturday 1st January 2022")

    def test_feast_upcoming_api_defaults_to_today(self):
        r = self.client.get(url_for("feast_upcoming_api"))
        self.assertEqual(200, r.status_code)
        self.assertTrue(r.get_json())

    def test_feast_upcoming_api_with_bad_date(self):
        r = self.client.get(url_for("feast_upcoming_api") + "?date=not-a-date")
        self.assertEqual(400, r.status_code)

    def test_feast_detail_view_handles_not_found(self):
        r = self.client.get(url_for("feast_detail_view", slug="notmas-day"))
        self.assertEqual(r.status_code, 404)

    @patch("pypew.views.feast_views.Feast.create_docx", side_effect=m_create_docx_impl)
    def test_feast_docx_view(self, m_create_docx):
        r = self.client.get(url_for("feast_docx_view", slug="christmas-day"))
        m_create_docx.assert_called()
        self.assertEqual(200, r.status_code)
        self.assertEqual(
            'attachment; filename="Christmas Day.docx"',
            r.headers["Content-Disposition"],
        )
        self.assertEqual(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            r.headers["Content-Type"],
        )

    @patch(
        "pypew.views.pew_sheet_views.Service.create_docx",
        side_effect=m_create_docx_impl,
    )
    def test_pew_sheet_docx_view(self, m_create_docx):
        r = self.client.get(
            url_for("pew_sheet_docx_view")
            + "?"
            + urlencode(
                {
                    "title": "Feast of Foo",
                    "date": "2022-01-01",
                    "time": "11:00",
                    "primary_feast": "advent-i",
                    "secondary_feasts": "trinity-iii",
                    "introit_hymn": "",
                    "offertory_hymn": "",
                    "recessional_hymn": "",
                    "anthem_group-translation": "",
                }
            )
        )
        self.assertEqual(r.status_code, 200)
        m_create_docx.assert_called()
        self.assertEqual(
            r.headers["Content-Disposition"],
            'attachment; filename="2022-01-01 Feast of Foo.docx"',
        )
        self.assertEqual(
            r.headers["Content-Type"],
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )


if __name__ == "__main__":
    unittest.main()
