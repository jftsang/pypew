import unittest

from flask import url_for

from pypew.pypew import create_app


class TestViews(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app()
        self.client = self.app.test_client()

    def test_index_view(self):
        with self.app.app_context():
            r = self.client.get(url_for('index_view'))
        self.assertEqual(r.status_code, 200)

    def test_service_index_view(self):
        with self.app.app_context():
            r = self.client.get(url_for('service_index_view'))
        self.assertEqual(r.status_code, 200)


if __name__ == '__main__':
    unittest.main()
