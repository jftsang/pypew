import datetime as dt
import unittest
from datetime import date
from unittest import TestCase
from unittest.mock import patch

from dateexpr import parse


class TestDateExpr(TestCase):
    def test_simple(self):
        orig_dt_date = dt.date
        with patch('datetime.date') as mock_date:
            mock_date.today.return_value = date(2026, 4, 5)
            mock_date.side_effect = lambda *args, **kw: orig_dt_date(*args, **kw)

            assert parse("Easter") == date(2026, 4, 5)
            assert parse("Easter", 2027) == date(2027, 3, 28)
            assert (
                parse("Easter Monday")
                == parse("day after Easter")
                == date(2026, 4, 6)
            )
            assert parse("14 November") == date(2026, 11, 14)
            assert parse("Christmas") == date(2026, 12, 25)
            assert parse("Christmas", 2014) == dt.date(2014, 12, 25)
            assert parse("Christmas") == parse("Christmas")

    def test_relative_days_and_weeks(self):
        assert parse("3 days before Easter", 2026) == date(2026, 4, 2)
        assert parse("3 days after Easter", 2026) == date(2026, 4, 8)
        assert parse("1 week after Easter", 2026) == date(2026, 4, 12)
        assert parse("2 week before Easter", 2026) == date(2026, 3, 22)

    def test_relative_weekdays(self):
        assert parse("Sunday after Easter", 2026) == date(2026, 4, 12)
        assert parse("Monday after Easter", 2026) == date(2026, 4, 6)
        assert parse("2 Mondays after Easter", 2026) == date(2026, 4, 13)
        assert parse("Monday before Easter", 2026) == date(2026, 3, 30)
        assert parse("2 Mondays before Easter", 2026) == date(2026, 3, 23)

    def test_nearest_weekdays(self):
        assert parse("Thursday nearest Easter", 2026) == date(2026, 4, 2)
        assert parse("Friday nearest Easter", 2026) == date(2026, 4, 3)
        assert parse("Saturday nearest Easter", 2026) == date(2026, 4, 4)
        assert parse("Sunday nearest Easter", 2026) == date(2026, 4, 5)  # same day
        assert parse("Monday nearest Easter", 2026) == date(2026, 4, 6)
        assert parse("Tuesday nearest Easter", 2026) == date(2026, 4, 7)
        assert parse("Wednesday nearest Easter", 2026) == date(2026, 4, 8)

    def test_complex_clauses(self):
        d = parse(
            "Sunday nearest 2 Mondays after 4th Sunday before Christmas Day",
            2026
        )
        assert d == parse("Sunday nearest 2 Mondays after Advent Sunday", 2026)
        assert d == parse("Sunday nearest 7 December")
        assert d == date(2026, 12, 6)

    def test_complex_clauses_handles_years(self):
        orig_dt_date = dt.date
        with patch('dateexpr.date') as mock_date:
            mock_date.today.return_value = date(2012, 4, 5)
            mock_date.side_effect = lambda *args, **kw: orig_dt_date(*args, **kw)

            d = parse(
                "Sunday nearest 2 Mondays after 4th Sunday before Christmas Day"
            )
            assert d == parse("Sunday nearest 2 Mondays after Advent Sunday")
            assert d == parse("Sunday nearest 7 December")
            assert d == date(2012, 12, 9)

    def test_aliases(self):
        assert (
            parse("Advent Sunday")
            == parse("4th Sunday before Christmas")
            == parse("4th Sunday before Christmas Day")
            == parse("4 Sundays before Christmas Day")
            == date(2026, 11, 29)
        )
        assert (
            parse("Remembrance Sunday", 2026)
            == parse("Sunday nearest 11 November", 2026)
            == date(2026, 11, 8)
        )


if __name__ == '__main__':
    unittest.main()
