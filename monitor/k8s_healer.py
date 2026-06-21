import logging
import os
import time

from kubernetes import client, config, watch
from monitor.db import record_event
from monitor.metrics import (
    container_up,
    container_restarts_total,
    container_failures_total,
)
from monitor.notifiers import notify_all

NAMESPACES = os.getenv("MONITORED_NAMESPACES", "default").split(",")
RETRY_LIMIT = int(os.getenv("RETRY_LIMIT", "3"))


def load_k8s_config():
    try:
        config.load_incluster_config()      # inside a Pod on K8s
        logging.info("[K8s] Using in-cluster config")
    except Exception:
        config.load_kube_config()           # local kubeconfig (Minikube)
        logging.info("[K8s] Using local kubeconfig")


def restart_pod(namespace: str, pod_name: str, owner_name: str):
    """Delete the pod — the owning ReplicaSet/Deployment recreates it."""
    v1 = client.CoreV1Api()
    for attempt in range(1, RETRY_LIMIT + 1):
        try:
            v1.delete_namespaced_pod(name=pod_name, namespace=namespace)
            logging.info(f"[K8s][SUCCESS] Deleted pod {pod_name} (attempt {attempt}) — will be recreated")
            container_restarts_total.labels(container=pod_name).inc()
            record_event(pod_name, "restarted", attempt)
            notify_all(f"✅ [K8s] Pod {pod_name} deleted and will be recreated (attempt {attempt})")
            return True
        except Exception as e:
            if "404" in str(e) or "Not Found" in str(e):
                logging.info(f"[K8s] Pod {pod_name} already deleted — Kubernetes is recreating it")
                record_event(pod_name, "restarted", attempt)
                return True
            logging.warning(f"[K8s][RETRY {attempt}] Failed to delete pod {pod_name}: {e}")
            record_event(pod_name, f"retry_{attempt}_failed", attempt)
            time.sleep(5)

    logging.error(f"[K8s][CRITICAL] Pod {pod_name} could not be restarted after {RETRY_LIMIT} attempts")
    container_failures_total.labels(container=pod_name).inc()
    record_event(pod_name, "critical_failure", RETRY_LIMIT)
    notify_all(f"🚨 [K8s] CRITICAL: Pod {pod_name} failed to restart after {RETRY_LIMIT} attempts")
    return False


def get_pod_owner(namespace: str, pod) -> str:
    refs = pod.metadata.owner_references or []
    return refs[0].name if refs else "standalone"


def watch_pods(namespace: str):
    v1 = client.CoreV1Api()
    w = watch.Watch()
    logging.info(f"[K8s] Watching pods in namespace: {namespace}")

    for event in w.stream(v1.list_namespaced_pod, namespace=namespace, timeout_seconds=0):
        pod = event["object"]
        event_type = event["type"]
        pod_name = pod.metadata.name
        phase = pod.status.phase or "Unknown"

        # skip monitor/dashboard pods to avoid self-healing loops
        if any(skip in pod_name for skip in ["monitor", "dashboard", "prometheus", "grafana"]):
            continue

        is_up = phase == "Running" and all(
            (cs.ready if cs.ready is not None else False)
            for cs in (pod.status.container_statuses or [])
        )
        container_up.labels(container=pod_name).set(1 if is_up else 0)

        if event_type in ("MODIFIED", "ADDED"):
            if phase in ("Failed", "Unknown"):
                owner = get_pod_owner(namespace, pod)
                logging.warning(f"[K8s][ALERT] Pod {pod_name} is {phase} (owner: {owner}). Restarting...")
                notify_all(f"⚠️ [K8s] Pod {pod_name} is {phase}. Attempting restart...")
                record_event(pod_name, f"pod_{phase.lower()}", 0)
                restart_pod(namespace, pod_name, owner)

            # detect crash loop
            for cs in (pod.status.container_statuses or []):
                if cs.restart_count and cs.restart_count >= 5:
                    logging.warning(f"[K8s][CRASHLOOP] {pod_name} container {cs.name} restarted {cs.restart_count}x")
                    notify_all(f"🔁 [K8s] CrashLoop detected: {pod_name} restarted {cs.restart_count} times")
                    record_event(pod_name, "crashloop_detected", cs.restart_count)


def run_k8s_monitor():
    load_k8s_config()
    import threading
    threads = [
        threading.Thread(target=watch_pods, args=(ns.strip(),), daemon=True)
        for ns in NAMESPACES
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
