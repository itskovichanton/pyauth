import threading
from collections import UserDict


class ThreadSafeImmutableDict(UserDict):

    def __init__(self, dict=None, /, **kwargs):
        super().__init__(dict=dict, **kwargs)
        self.data_lock = threading.Lock()

    def __setitem__(self, key, value):
        with self.data_lock:
            if key in self:
                raise ValueError(f'Key {key} already exists')
            super().__setitem__(key, value)
