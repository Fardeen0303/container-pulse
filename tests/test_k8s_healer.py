from unittest.mock import MagicMock, patch


@patch("monitor.k8s_healer.notify_all")
@patch("monitor.k8s_healer.record_event")
@patch("monitor.k8s_healer.client")
def test_restart_pod_success(mock_k8s_client, mock_record, mock_notify):
    mock_v1 = MagicMock()
    mock_k8s_client.CoreV1Api.return_value = mock_v1

    from monitor.k8s_healer import restart_pod
    result = restart_pod("default", "flask-app-abc123", "flask-app")

    assert result is True
    mock_v1.delete_namespaced_pod.assert_called_once_with(name="flask-app-abc123", namespace="default")
    mock_record.assert_called_with("flask-app-abc123", "restarted", 1)
    mock_notify.assert_called_once()


@patch("monitor.k8s_healer.notify_all")
@patch("monitor.k8s_healer.record_event")
@patch("monitor.k8s_healer.time")
@patch("monitor.k8s_healer.client")
def test_restart_pod_all_attempts_fail(mock_k8s_client, mock_time, mock_record, mock_notify):
    mock_v1 = MagicMock()
    mock_v1.delete_namespaced_pod.side_effect = Exception("forbidden")
    mock_k8s_client.CoreV1Api.return_value = mock_v1

    from monitor.k8s_healer import restart_pod
    result = restart_pod("default", "nginx-xyz", "nginx")

    assert result is False
    assert mock_v1.delete_namespaced_pod.call_count == 3
    mock_record.assert_called_with("nginx-xyz", "critical_failure", 3)
    assert any("CRITICAL" in str(c) for c in mock_notify.call_args_list)


def test_get_pod_owner_with_owner_ref():
    from monitor.k8s_healer import get_pod_owner
    pod = MagicMock()
    owner = MagicMock()
    owner.name = "flask-app-replicaset"
    pod.metadata.owner_references = [owner]
    assert get_pod_owner("default", pod) == "flask-app-replicaset"


def test_get_pod_owner_standalone():
    from monitor.k8s_healer import get_pod_owner
    pod = MagicMock()
    pod.metadata.owner_references = []
    assert get_pod_owner("default", pod) == "standalone"
