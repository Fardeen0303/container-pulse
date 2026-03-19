# Container-Pulse

Automated self-healing Docker infrastructure with real-time monitoring, alerting, and observability.

## Features
- Real-time container health monitoring
- Automatic restart with retry logic (3 attempts)
- Slack alerts on failure and recovery
- Prometheus metrics + Grafana dashboard
- GitHub Actions CI/CD pipeline
- Structured logging to file

## Tech Stack
- Python 3 + Docker SDK
- Docker Compose
- Prometheus + Grafana
- Slack Webhook
- GitHub Actions

## Setup

1. Clone the repository
   ```
   git clone https://github.com/yourusername/container-pulse.git
   cd container-pulse
   ```

2. Add your Slack webhook in `.env`
   ```
   SLACK_WEBHOOK=https://hooks.slack.com/services/your/webhook/url
   ```

3. Run everything
   ```
   docker-compose up -d --build
   ```

## Test Self-Healing

```
docker stop devops-container
docker logs -f monitor
```

Monitor will auto-restart it within 20 seconds.

## Services

| Service    | URL                    |
|------------|------------------------|
| Flask App  | http://localhost:5000  |
| Nginx      | http://localhost:8080  |
| Prometheus | http://localhost:9090  |
| Grafana    | http://localhost:3000  |

## Project Structure

```
container-pulse/
├── app/               # Flask application
├── monitor/           # Self-healing monitor
├── prometheus/        # Prometheus config
├── tests/             # Unit tests
├── .github/workflows/ # CI/CD pipeline
├── logs/              # Monitor logs
└── docker-compose.yml
```

## Skills Demonstrated
- Infrastructure automation
- Container orchestration
- Python scripting
- System monitoring
- Observability (Prometheus + Grafana)
- CI/CD (GitHub Actions)
- Reliability engineering
