"""Интеграционные тесты RedisSessionStorage. Нужен Redis на localhost:6379."""
from __future__ import annotations

import time
import unittest
from types import SimpleNamespace

import redis

from src.mybootstrap_core_itskovichanton.redis_service import RedisConfig, RedisService
from src.mybootstrap_mvc_itskovichanton.exceptions import CoreException
from src.mybootstrap_pyauth_itskovichanton.backend.session_storage import (
    RedisSessionStorage,
    SimpleTokenFactory,
)
from src.mybootstrap_pyauth_itskovichanton.entities import Session, User


class _Cfg:
    def app_name(self) -> str:
        return f"pyauth_test_{int(time.time() * 1000)}"

    def get_config(self):
        return SimpleNamespace(full_name=self.app_name)


def _redis_up() -> bool:
    try:
        redis.Redis(host="localhost", port=6379).ping()
        return True
    except Exception:
        return False


def _build_storage() -> RedisSessionStorage:
    redis_svc = RedisService.__new__(RedisService)
    redis_svc.config = RedisConfig(host="localhost", port=6379, password=None)
    redis_svc.config_service = _Cfg()

    storage = RedisSessionStorage.__new__(RedisSessionStorage)
    storage.token_factory = SimpleTokenFactory()
    storage.config_service = redis_svc.config_service
    storage.redis_service = redis_svc
    storage.session_ttl_sec = 3600
    storage.init()
    return storage


@unittest.skipUnless(_redis_up(), "Redis не запущен")
class RedisSessionStorageTest(unittest.TestCase):

    def setUp(self):
        self.storage = _build_storage()
        self.user = User(username="alice", password="secret-hash", role="regular-user", slug="a")

    def tearDown(self):
        self.storage.logout_all()

    def test_assign_and_find_by_token(self):
        session = self.storage.assign_session(self.user)
        self.assertTrue(len(session.token) >= 32)
        self.assertIsNone(session.account.password)

        found = self.storage.find_session(Session(token=session.token))
        self.assertEqual(found.account.username, "alice")
        self.assertIsNone(found.account.password)

    def test_find_by_username_and_single_session(self):
        first = self.storage.assign_session(self.user)
        second = self.storage.assign_session(self.user)
        self.assertNotEqual(first.token, second.token)
        self.assertIsNone(self.storage.find_session(Session(token=first.token)))
        found = self.storage.find_session(Session(account=User(username="alice", slug="a")))
        self.assertEqual(found.token, second.token)

    def test_logout(self):
        session = self.storage.assign_session(self.user)
        self.storage.logout(Session(token=session.token))
        self.assertIsNone(self.storage.find_session(Session(token=session.token)))

    def test_logout_all_does_not_need_flushdb(self):
        self.storage.assign_session(self.user)
        self.storage.logout_all()
        self.assertEqual(self.storage.get_token_to_session_storage(), {})
        self.assertEqual(self.storage.get_username_to_token_storage(), {})

    def test_forced_token_too_short_rejected(self):
        with self.assertRaises(CoreException):
            self.storage.assign_session(self.user, forced_session_token="short")

    def test_password_not_stored_in_dump(self):
        self.storage.assign_session(self.user)
        dump = self.storage.get_token_to_session_storage()
        for session in dump.values():
            self.assertTrue(session.account.password in (None, ""))


if __name__ == "__main__":
    unittest.main()
