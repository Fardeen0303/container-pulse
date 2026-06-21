import logging
import time
import docker

from monitor.metrics import (
    container_restarts_total,
    container_failures_total,
    cpu_usage_percent,
    memory_usage_percent,
)
from monitor.notifiers import notify_all
from monitor.db import record_event

RETRY_LIMIT = 3
CPU_WARN_THRESHOLD = 80.0
MEM_WARN_THRESHOLD = 85.0

client = docker.from_env()


def collect_resource_stats(name: str):
    """Collect CPU and memory stats and update metrics. Warn if thresholds exceeded."""
    try:
        container = client.containers.get(name)
        if container.status != "running":
            return
        stats = container.stats(stream=False)

        cpu_delta = (stats["cpu_stats"]["cpu_usage"]["total_usage"]
                     - stats["precpu_stats"]["cpu_usage"]["total_usage"])
        system_delta = (stats["cpu_stats"]["system_cpu_usage"]
                        - stats["precpu_stats"]["system_cpu_usage"])
        num_cpus = stats["cpu_stats"].get("online_cpus", 1)
        cpu = (cpu_delta / system_delta) * num_cpus * 100.0 if system_delta > 0 else 0.0

        mem_used = stats["memory_stats"]["usage"]
        mem_limit = stats["memory_stats"]["limit"]
        mem = (mem_used / mem_limit) * 100.0 if mem_limit > 0 else 0.0

        cpu_usage_percent.labels(container=name).set(round(cpu, 2))
        memory_usage_percent.labels(container=name).set(round(mem, 2))

        if cpu > CPU_WARN_THRESHOLD:
            logging.warning(f"[PREDICT] {name} CPU at {cpu:.1f}% — may fail soon")
            notify_all(f"⚠️ [Prediction] {name} CPU usage at {cpu:.1f}% — possible failure incoming")

        if mem > MEM_WARN_THRESHOLD:
            logging.warning(f"[PREDICT] {name} memory at {mem:.1f}% — may fail soon")
            notify_all(f"⚠️ [Prediction] {name} memory at {mem:.1f}% — possible failure incoming")

    except Exception as e:
        logging.debug(f"[Stats] Could not collect stats for {name}: {e}")


def restart_container(name: str):
    for attempt in range(1, RETRY_LIMIT + 1):
        try:
            client.containers.get(name).start()
            logging.info(f"[SUCCESS] {name} restarted on attempt {attempt}")
            container_restarts_total.labels(container=name).inc()
            record_event(name, "restarted", attempt)
            notify_all(f"✅ {name} restarted successfully (attempt {attempt})")
            return True
        except Exception as e:
            logging.warning(f"[RETRY {attempt}] Failed to restart {name}: {e}")
            record_event(name, f"retry_{attempt}_failed", attempt)
            time.sleep(5)

    logging.error(f"[CRITICAL] {name} failed after {RETRY_LIMIT} attempts")
    container_failures_total.labels(container=name).inc()
    record_event(name, "critical_failure", RETRY_LIMIT)
    notify_all(f"🚨 CRITICAL: {name} failed to restart after {RETRY_LIMIT} attempts")
    return False
