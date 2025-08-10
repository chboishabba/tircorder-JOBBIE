import queue
import threading
from rate_limit import FixedRateLimiter
from cpu_monitor import CPUMonitor


class QueryQueueManager:
    """Processes callables sequentially while obeying a rate limit."""

    def __init__(self, rate_limiter: FixedRateLimiter | None = None,
                 cpu_monitor: CPUMonitor | None = None):
        self._queue = queue.Queue()
        self._rate_limiter = rate_limiter or FixedRateLimiter(0)
        self._cpu_monitor = cpu_monitor
        self._worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker.start()

    def enqueue(self, func, *args, **kwargs):
        """Schedule a callable to be executed."""
        self._queue.put((func, args, kwargs))

    def join(self):
        self._queue.join()

    def _worker_loop(self):
        while True:
            func, args, kwargs = self._queue.get()
            try:
                if self._cpu_monitor:
                    self._cpu_monitor.wait_for_safe_usage()
                self._rate_limiter.wait()
                func(*args, **kwargs)
            finally:
                self._queue.task_done()
