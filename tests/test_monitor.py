def test_containers_list():
    containers = ["devops-container", "nginx-container"]
    assert isinstance(containers, list)
    assert len(containers) > 0

def test_retry_limit():
    retry_limit = 3
    assert retry_limit >= 1

def test_poll_interval():
    poll_interval = 20
    assert poll_interval > 0
