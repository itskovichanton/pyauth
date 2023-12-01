import pickle
import threading
from collections import UserDict
from dataclasses import asdict
from typing import Dict, Callable

from redis.client import Redis

from src.mybootstrap_pyauth_itskovichanton.entities import Session, User


class ThreadSafeImmutableDict(UserDict):

    def __init__(self, dict=None, /, **kwargs):
        super().__init__(dict=dict, **kwargs)
        self.data_lock = threading.Lock()

    def __setitem__(self, key, value):
        with self.data_lock:
            if key in self:
                raise ValueError(f'Key {key} already exists')
            super().__setitem__(key, value)


class RedisSessionMap:
    def __init__(self, rds: Redis, key_prefix: str):
        self.key_prefix = key_prefix
        self.user_class = User
        self.rds = rds

    def _make_key(self, key: str) -> str:
        return f"{self.key_prefix}:{key}"

    def get(self, key: str) -> Session | None:
        session_bytes = self.rds.get(self._make_key(key))
        if session_bytes is None:
            return None
        session_dict = pickle.loads(session_bytes)
        session = Session(**session_dict)
        # account = dacite.from_dict(data_class=self.user_class, data=session.account, config=Config(check_types=False))
        account = self.user_class(**session.account)
        return Session(token=session.token, account=account)

    def set(self, key: str, session: Session) -> None:
        session_dict = asdict(session)
        session_bytes = pickle.dumps(session_dict)
        self.rds.set(self._make_key(key), session_bytes)

    def delete(self, key: str):
        return self.rds.delete(self._make_key(key))

    def get_all(self) -> Dict[str, Session]:
        keys = self.rds.keys(f"{self.key_prefix}:*")
        result = {}
        for key in keys:
            key_str = key.decode('utf-8')
            session_bytes = self.rds.get(key_str)
            session_dict = pickle.loads(session_bytes)
            session = Session(**session_dict)
            result[key_str[len(self.key_prefix) + 1:]] = session
        return result

    def set_user_class(self, user_class):
        self.user_class = user_class

    def clear(self):
        self.rds.delete(self.key_prefix)

    def update(self, token: str, updater: Callable[[Session, ], None]) -> Session:
        v = self.get(token)
        updater(v)
        self.set(token, v)
        return self.get(token)


class RedisStringMap:
    def __init__(self, rds: Redis, key_prefix: str):
        self.key_prefix = key_prefix
        self.rds = rds

    def _make_key(self, key: str) -> str:
        return f"{self.key_prefix}:{key}"

    def get(self, key: str) -> str:
        r = self.rds.get(self._make_key(key))
        if r is not None:
            return str(r)

    def set(self, key: str, value: str) -> None:
        self.rds.set(self._make_key(key), value)

    def delete(self, key: str) -> None:
        self.rds.delete(self._make_key(key))

    def get_all(self) -> Dict[str, str]:
        keys = self.rds.keys(f"{self.key_prefix}:*")
        result = {}
        for key in keys:
            key_str = key.decode('utf-8')
            result[key_str[len(self.key_prefix) + 1:]] = self.rds.get(key_str)
        return result

    def clear(self):
        self.rds.delete(self.key_prefix)
