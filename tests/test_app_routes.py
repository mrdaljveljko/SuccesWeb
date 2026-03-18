import unittest

from app import app


class AstroAppRouteTests(unittest.TestCase):
    def test_only_astroai_routes_remain(self):
        route_rules = {
            rule.rule
            for rule in app.url_map.iter_rules()
            if not rule.rule.startswith('/static')
        }

        self.assertEqual(
            route_rules,
            {
                '/',
                '/register',
                '/login',
                '/forgot-password',
                '/logout',
                '/dashboard',
                '/horoscope',
                '/ask',
                '/meditation',
                '/tokens',
                '/upgrade',
                '/profile',
            },
        )

    def test_old_sourceai_routes_are_gone(self):
        client = app.test_client()
        self.assertEqual(client.get('/api/analyze').status_code, 404)
        self.assertEqual(client.get('/api/export').status_code, 404)


if __name__ == '__main__':
    unittest.main()
