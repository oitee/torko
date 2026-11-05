"""Keep calls at a steady rate across threads."""
from __future__ import annotations

import threading
import time


class Pace:
    def __init__(self, per_second: float, clock=time.monotonic, sleep=time.sleep):
        self.gap = 1.0 / per_second
        self.clock, self.sleep = clock, sleep
        self.next_at = 0.0
        self.lock = threading.Lock()

    def wait(self) -> None:
        with self.lock:
            now = self.clock()
            at = max(now, self.next_at)
            self.next_at = at + self.gap
        if at > now:
            self.sleep(at - now)
