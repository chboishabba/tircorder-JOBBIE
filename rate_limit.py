import time
import math

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
