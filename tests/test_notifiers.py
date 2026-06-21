from unittest.mock import patch, MagicMock
import os


def test_slack_skips_if_no_webhook():
    with patch.dict(os.environ, {"SLACK_WEBHOOK": ""}):
        from monitor.notifiers import SlackNotifier
        n = SlackNotifier()
        n.send("test")  # should silently skip


@patch("slack_sdk.webhook.WebhookClient")
def test_slack_sends_when_webhook_set(mock_wh):
    with patch.dict(os.environ, {"SLACK_WEBHOOK": "https://hooks.slack.com/test"}):
        from monitor.notifiers import SlackNotifier
        n = SlackNotifier()
        n.send("alert!")
        mock_wh.return_value.send.assert_called_once_with(text="alert!")


def test_notify_all_calls_all_notifiers():
    with patch("monitor.notifiers.get_notifiers") as mock_get:
        mock_n1, mock_n2 = MagicMock(), MagicMock()
        mock_get.return_value = [mock_n1, mock_n2]
        from monitor.notifiers import notify_all
        notify_all("broadcast")
        mock_n1.send.assert_called_once_with("broadcast")
        mock_n2.send.assert_called_once_with("broadcast")
