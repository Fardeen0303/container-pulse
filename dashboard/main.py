import os  # noqa: E402
import sys  # noqa: E402

sys.path.insert(0, "/app")  # noqa: E402

from fastapi import FastAPI  # noqa: E402
from fastapi.requests import Request  # noqa: E402
from fastapi.responses import HTMLResponse  # noqa: E402
from fastapi.templating import Jinja2Templates  # noqa: E402
from monitor.db import get_recent_incidents, get_restart_counts  # noqa: E402

app = FastAPI(title="Container-Pulse Dashboard")
templates = Jinja2Templates(directory="/app/dashboard/templates")

MODE = os.getenv("MODE", "docker")


def get_container_statuses():
    import docker
    docker_client = docker.from_env()
    monitored = os.getenv("MONITORED_CONTAINERS", "devops-container,nginx-container").split(",")
    running = {c.name: c for c in docker_client.containers.list(all=True)}
    return [
        {
            "name": name,
            "status": running[name].status if name in running else "missing",
            "image": running[name].image.tags[0] if name in running and running[name].image.tags else "unknown",
        }
        for name in monitored
    ]


def get_pod_statuses():
    from kubernetes import client, config
    try:
        config.load_incluster_config()
    except Exception:
        config.load_kube_config()

    v1 = client.CoreV1Api()
    namespaces = os.getenv("MONITORED_NAMESPACES", "default").split(",")
    pods = []
    for ns in namespaces:
        for pod in v1.list_namespaced_pod(ns.strip()).items:
            phase = pod.status.phase or "Unknown"
            restarts = sum(
                cs.restart_count for cs in (pod.status.container_statuses or [])
            )
            pods.append({
                "name": pod.metadata.name,
                "namespace": ns.strip(),
                "status": phase.lower(),
                "image": pod.spec.containers[0].image if pod.spec.containers else "unknown",
                "restarts": restarts,
            })
    return pods


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    containers = get_pod_statuses() if MODE == "kubernetes" else get_container_statuses()
    return templates.TemplateResponse(request, "index.html", {
        "containers": containers,
        "incidents": get_recent_incidents(20),
        "restart_counts": get_restart_counts(),
        "mode": MODE,
    })


@app.get("/api/containers")
def api_containers():
    return get_container_statuses() if MODE == "docker" else []


@app.get("/api/pods")
def api_pods():
    return get_pod_statuses() if MODE == "kubernetes" else []


@app.get("/api/incidents")
def api_incidents():
    return get_recent_incidents(50)


@app.get("/api/summary")
def api_summary():
    return {
        "mode": MODE,
        "restart_counts": get_restart_counts(),
        "recent_incidents": get_recent_incidents(10),
    }
