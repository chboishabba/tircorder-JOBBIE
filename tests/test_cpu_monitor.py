import cpu_monitor


def test_cpu_monitor_waits(monkeypatch):
    """High CPU usage should cause the monitor to sleep until safe."""
    usage_readings = [90, 50]

    def fake_cpu_percent(interval):
        return usage_readings.pop(0)

    sleeps = []

    def fake_sleep(seconds):
        sleeps.append(seconds)

    monkeypatch.setattr(cpu_monitor.psutil, "cpu_percent", fake_cpu_percent)
    monkeypatch.setattr(cpu_monitor.time, "sleep", fake_sleep)

    messages = []
    monkeypatch.setattr("builtins.print", lambda msg: messages.append(msg))

    monitor = cpu_monitor.CPUMonitor(max_percent=70, check_interval=0.01)
    monitor.wait_for_safe_usage()

    assert sleeps == [0.01]
    assert messages and "throttling" in messages[0]
