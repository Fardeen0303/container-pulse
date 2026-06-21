import logging
import os
import time

from prometheus_client import start_http_server

from monitor.db import init_db
from monitor.metrics import container_up, health_checks_total

CONTAINERS = os.getenv("MONITORED_CONTAINERS", "devops-container,nginx-container").split(",")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "20"))
MODE = os.getenv("MODE", "docker")          # "docker" or "kubernetes"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler("/app/logs/monitor.log"),
        logging.StreamHandler(),
    ],
)


def run_docker_monitor():
    import docker
    from monitor.healer import collect_resource_stats, restart_container
    from monitor.notifiers import notify_all

    client = docker.from_env()
    logging.info(f"[Docker] Monitoring: {', '.join(CONTAINERS)}")

    while True:
        running = [c.name for c in client.containers.list()]
        health_checks_total.inc()

        for name in CONTAINERS:
            is_up = name in running
            container_up.labels(container=name).set(1 if is_up else 0)

            if is_up:
                collect_resource_stats(name)
            else:
                logging.warning(f"[ALERT] {name} is down. Restarting...")
                notify_all(f"⚠️ {name} is down. Attempting restart...")
                restart_container(name)

        time.sleep(POLL_INTERVAL)


def main():
    init_db()
    start_http_server(8000)
    logging.info(f"Container-Pulse starting in [{MODE}] mode")

    if MODE == "kubernetes":
        from monitor.k8s_healer import run_k8s_monitor
        run_k8s_monitor()
    else:
        run_docker_monitor()


if __name__ == "__main__":
    main()
