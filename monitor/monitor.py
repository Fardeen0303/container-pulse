import docker
import time
import logging
import os
from slack_sdk.webhook import WebhookClient
from prometheus_client import start_http_server, Counter, Gauge

CONTAINERS = ["devops-container", "nginx-container"]
RETRY_LIMIT = 3
POLL_INTERVAL = 20
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK", "")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler("/app/logs/monitor.log"),
        logging.StreamHandler()
    ]
)

client = docker.from_env()
restart_counter = Counter("container_restarts_total", "Total restarts", ["container"])
container_status = Gauge("container_up", "Container status", ["container"])

def send_slack_alert(msg):
    if SLACK_WEBHOOK:
        WebhookClient(SLACK_WEBHOOK).send(text=msg)

def restart_container(name):
    for attempt in range(1, RETRY_LIMIT + 1):
        try:
            client.containers.get(name).start()
            logging.info(f"[SUCCESS] {name} restarted on attempt {attempt}")
            restart_counter.labels(container=name).inc()
            send_slack_alert(f"✅ {name} restarted successfully")
            return
        except Exception as e:
            logging.warning(f"[RETRY {attempt}] Failed to restart {name}: {e}")
            time.sleep(5)
    logging.error(f"[CRITICAL] {name} failed after {RETRY_LIMIT} attempts")
    send_slack_alert(f"🚨 CRITICAL: {name} failed to restart after {RETRY_LIMIT} attempts")

def monitor():
    start_http_server(8000)
    logging.info(f"Monitoring: {', '.join(CONTAINERS)}")
    while True:
        running = [c.name for c in client.containers.list()]
        for name in CONTAINERS:
            is_up = name in running
            container_status.labels(container=name).set(1 if is_up else 0)
            if not is_up:
                logging.warning(f"[ALERT] {name} is down. Restarting...")
                send_slack_alert(f"⚠️ {name} is down. Attempting restart...")
                restart_container(name)
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    monitor()
