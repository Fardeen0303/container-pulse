from unittest.mock import patch


@patch("monitor.healer.notify_all")
@patch("monitor.healer.record_event")
@patch("monitor.healer.client")
def test_restart_success_on_first_attempt(mock_client, mock_record, mock_notify):
    mock_client.containers.get.return_value.start.return_value = None

    from monitor.healer import restart_container
    result = restart_container("devops-container")

    assert result is True
    mock_client.containers.get.assert_called_once_with("devops-container")
    mock_record.assert_called_with("devops-container", "restarted", 1)
    mock_notify.assert_called_with("✅ devops-container restarted successfully (attempt 1)")


@patch("monitor.healer.notify_all")
@patch("monitor.healer.record_event")
@patch("monitor.healer.time")
@patch("monitor.healer.client")
def test_restart_succeeds_on_second_attempt(mock_client, mock_time, mock_record, mock_notify):
    mock_client.containers.get.return_value.start.side_effect = [Exception("not running"), None]

    from monitor.healer import restart_container
    result = restart_container("devops-container")

    assert result is True
    assert mock_client.containers.get.return_value.start.call_count == 2
    mock_record.assert_any_call("devops-container", "retry_1_failed", 1)
    mock_record.assert_any_call("devops-container", "restarted", 2)


@patch("monitor.healer.notify_all")
@patch("monitor.healer.record_event")
@patch("monitor.healer.time")
@patch("monitor.healer.client")
def test_restart_fails_all_attempts(mock_client, mock_time, mock_record, mock_notify):
    mock_client.containers.get.return_value.start.side_effect = Exception("dead")

    from monitor.healer import restart_container
    result = restart_container("devops-container")

    assert result is False
    assert mock_client.containers.get.return_value.start.call_count == 3
    mock_record.assert_called_with("devops-container", "critical_failure", 3)
    assert any("CRITICAL" in str(c) for c in mock_notify.call_args_list)


@patch("monitor.healer.notify_all")
@patch("monitor.healer.client")
def test_cpu_warning_triggers_alert(mock_client, mock_notify):
    mock_client.containers.get.return_value.status = "running"
    mock_client.containers.get.return_value.stats.return_value = {
        "cpu_stats": {
            "cpu_usage": {"total_usage": 900_000_000},
            "system_cpu_usage": 1_000_000_000,
            "online_cpus": 1,
        },
        "precpu_stats": {
            "cpu_usage": {"total_usage": 0},
            "system_cpu_usage": 0,
        },
        "memory_stats": {"usage": 100, "limit": 1000},
    }

    from monitor.healer import collect_resource_stats
    collect_resource_stats("devops-container")

    assert any("CPU" in str(c) for c in mock_notify.call_args_list)
