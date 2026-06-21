import os
import smtplib
import logging
from email.mime.text import MIMEText
from monitor.metrics import alerts_sent_total


class BaseNotifier:
    def send(self, msg: str):
        raise NotImplementedError


class SlackNotifier(BaseNotifier):
    def __init__(self):
        self.webhook = os.getenv("SLACK_WEBHOOK", "")

    def send(self, msg: str):
        if not self.webhook:
            return
        try:
            from slack_sdk.webhook import WebhookClient
            WebhookClient(self.webhook).send(text=msg)
            alerts_sent_total.labels(channel="slack").inc()
        except Exception as e:
            logging.warning(f"[Slack] Failed to send alert: {e}")


class EmailNotifier(BaseNotifier):
    def __init__(self):
        self.host = os.getenv("SMTP_HOST", "")
        self.port = int(os.getenv("SMTP_PORT", "587"))
        self.user = os.getenv("SMTP_USER", "")
        self.password = os.getenv("SMTP_PASSWORD", "")
        self.recipient = os.getenv("ALERT_EMAIL", "")

    def send(self, msg: str):
        if not all([self.host, self.user, self.password, self.recipient]):
            return
        try:
            mail = MIMEText(msg)
            mail["Subject"] = "Container-Pulse Alert"
            mail["From"] = self.user
            mail["To"] = self.recipient
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.sendmail(self.user, self.recipient, mail.as_string())
            alerts_sent_total.labels(channel="email").inc()
        except Exception as e:
            logging.warning(f"[Email] Failed to send alert: {e}")


def get_notifiers() -> list[BaseNotifier]:
    return [SlackNotifier(), EmailNotifier()]


def notify_all(msg: str):
    for notifier in get_notifiers():
        notifier.send(msg)
