from prometheus_client import Counter, Gauge

container_up = Gauge("container_up", "Container running status", ["container"])
container_restarts_total = Counter("container_restarts_total", "Total restart attempts", ["container"])
container_failures_total = Counter("container_failures_total", "Total unrecoverable failures", ["container"])
health_checks_total = Counter("health_checks_total", "Total health check cycles performed")
alerts_sent_total = Counter("alerts_sent_total", "Total alerts sent", ["channel"])
cpu_usage_percent = Gauge("container_cpu_percent", "Container CPU usage percent", ["container"])
memory_usage_percent = Gauge("container_memory_percent", "Container memory usage percent", ["container"])
