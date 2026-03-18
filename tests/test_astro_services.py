import sqlite3
import unittest
from datetime import datetime

from astro_services import AstroService


class AstroServiceTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        self.conn.row_factory = sqlite3.Row
        self.service = AstroService(self.conn)
        self.service.initialize()
        self.now = datetime(2026, 3, 18, 8, 0, 0)
        self.service.utcnow = lambda: self.now  # type: ignore[method-assign]
        self.user = self.service.create_user(
            name='Nova',
            email='nova@example.com',
            password_hash='hash',
            zodiac_sign='Aries',
            birth_date=None,
        )

    def test_login_reward_claimed_once_per_day(self):
        first = self.service.record_login_reward(self.user['id'])
        second = self.service.record_login_reward(self.user['id'])
        user = self.service.get_user(self.user['id'])

        self.assertTrue(first['claimed'])
        self.assertFalse(second['claimed'])
        self.assertEqual(user['astro_token_balance'], 5)
        self.assertEqual(user['streak_count'], 1)

    def test_streak_resets_after_missed_day(self):
        self.service.record_login_reward(self.user['id'])
        self.now = datetime(2026, 3, 20, 8, 0, 0)
        reward = self.service.record_login_reward(self.user['id'])
        user = self.service.get_user(self.user['id'])

        self.assertTrue(reward['claimed'])
        self.assertEqual(user['streak_count'], 1)

    def test_free_user_day_one_question_then_token_unlock(self):
        access = self.service.question_access(self.user)
        self.assertTrue(access.allowed)
        self.service.submit_question(self.user, 'What energy should I protect?', access.source_type)
        access_after = self.service.question_access(self.service.get_user(self.user['id']))
        self.assertFalse(access_after.allowed)
        self.assertTrue(access_after.requires_tokens)

    def test_spend_tokens_never_goes_negative(self):
        ok, message = self.service.spend_tokens(self.user['id'], 'extra_question', 10)
        self.assertFalse(ok)
        self.assertIn('need 10 Astro Tokens', message)

    def test_weekly_meditation_tracking_for_free_user(self):
        access = self.service.meditation_access(self.user)
        self.assertTrue(access.allowed)
        meditation = self.service.list_meditations()[0]
        self.service.consume_meditation(self.user['id'], meditation['id'])
        access_after = self.service.meditation_access(self.service.get_user(self.user['id']))
        self.assertFalse(access_after.allowed)


if __name__ == '__main__':
    unittest.main()
