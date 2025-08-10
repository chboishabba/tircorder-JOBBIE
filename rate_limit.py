import time
import math
import threading

class RateLimiter:
    def __init__(self, max_interval=60, decay_function=None):
        self.counter = 0
        self.max_interval = max_interval
        self.decay_function = decay_function if decay_function else self.default_decay

    def increment(self):
        self.counter += 1

    def reset(self):
        self.counter = 0

    def sleep(self):
        interval = self.decay_function(self.counter)
        interval = min(interval, self.max_interval)
        time.sleep(interval)

    @staticmethod
    def default_decay(counter):
        # Exponential backoff
        return min(2 ** counter, 60)


class FixedRateLimiter:
    """Simple rate limiter that enforces a minimum interval between calls."""

    def __init__(self, interval_seconds):
        self.interval = interval_seconds
        self._lock = threading.Lock()
        self._last = 0.0

    def wait(self):
        with self._lock:
            now = time.time()
            remaining = self.interval - (now - self._last)
            if remaining > 0:
                time.sleep(remaining)
            self._last = time.time()
