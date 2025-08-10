import time
from query_queue import QueryQueueManager
from rate_limit import FixedRateLimiter
from cpu_monitor import CPUMonitor


def test_query_queue_respects_order_and_rate():
    timestamps = []

    def record(i):
        timestamps.append((i, time.time()))

    limiter = FixedRateLimiter(0.05)
    queue = QueryQueueManager(rate_limiter=limiter)
    for i in range(3):
        queue.enqueue(record, i)
    queue.join()

    # Ensure tasks executed in order
    assert [idx for idx, _ in timestamps] == [0, 1, 2]

    # Ensure rate limiting enforced
    intervals = [timestamps[i + 1][1] - timestamps[i][1] for i in range(len(timestamps) - 1)]
    assert all(delta >= 0.045 for delta in intervals)


def test_query_queue_uses_cpu_monitor(monkeypatch):
    calls = []

    class DummyMonitor(CPUMonitor):
        def __init__(self):
            pass

        def wait_for_safe_usage(self):
            calls.append("called")

    queue = QueryQueueManager(cpu_monitor=DummyMonitor())
    queue.enqueue(lambda: None)
    queue.join()
    assert calls == ["called"]
