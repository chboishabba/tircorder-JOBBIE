import time

try:  # pragma: no cover - exercised via stub in tests when psutil absent
    import psutil  # type: ignore
except Exception:  # pragma: no cover
    class _PsutilStub:
        def cpu_percent(self, interval: float) -> float:  # pragma: no cover - simple fallback
            return 0.0

    psutil = _PsutilStub()


class CPUMonitor:
    """Watches system CPU usage and blocks while it exceeds a threshold."""

    def __init__(self, max_percent: float = 85.0, check_interval: float = 0.5):
        """
        Parameters
        ----------
        max_percent: float
            Maximum CPU usage percentage before throttling kicks in.
        check_interval: float
            Seconds to wait between rechecks while throttling.
        """
        self.max_percent = max_percent
        self.check_interval = check_interval

    def wait_for_safe_usage(self) -> None:
        """Block until CPU usage drops below ``max_percent``.

        Prints a notification each time throttling occurs to make it visible to
        the user that work is being delayed due to heavy load.
        """
        while True:
            usage = psutil.cpu_percent(interval=0.1)
            if usage < self.max_percent:
                break
            print(
                f"CPU usage {usage:.1f}% exceeds limit {self.max_percent}%; throttling"
            )
            time.sleep(self.check_interval)
