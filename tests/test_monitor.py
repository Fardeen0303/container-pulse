import sys
sys.path.insert(0, "monitor")

def test_containers_list():
    import monitor
    assert isinstance(monitor.CONTAINERS, list)
    assert len(monitor.CONTAINERS) > 0

def test_retry_limit():
    import monitor
    assert monitor.RETRY_LIMIT >= 1

def test_poll_interval():
    import monitor
    assert monitor.POLL_INTERVAL > 0
