#!/bin/bash
set -e
exec > /var/log/container-pulse-init.log 2>&1

echo "=== Container-Pulse Bootstrap ==="

# ── System updates ──────────────────────────────────────────────
apt-get update -y
apt-get install -y curl wget git apt-transport-https ca-certificates gnupg lsb-release

# ── Docker ──────────────────────────────────────────────────────
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
  > /etc/apt/sources.list.d/docker.list
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
systemctl enable docker
systemctl start docker
usermod -aG docker ubuntu

# ── kubectl ─────────────────────────────────────────────────────
curl -LO "https://dl.k8s.io/release/$(curl -sL https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# ── Minikube ────────────────────────────────────────────────────
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
install minikube-linux-amd64 /usr/local/bin/minikube

# ── Python 3.10 + pip ───────────────────────────────────────────
apt-get install -y python3 python3-pip
pip3 install docker slack-sdk prometheus-client requests fastapi uvicorn jinja2 kubernetes

# ── Clone Container-Pulse ────────────────────────────────────────
cd /home/ubuntu
git clone https://github.com/Fardeen0303/container-pulse.git
chown -R ubuntu:ubuntu container-pulse

# ── Start Minikube as ubuntu user ────────────────────────────────
sudo -u ubuntu bash -c "
  cd /home/ubuntu
  minikube start --driver=docker --cpus=2 --memory=2048
  eval \$(minikube docker-env)

  cd container-pulse
  docker build -f app/Dockerfile -t container-pulse-app:latest ./app
  docker build -f monitor/Dockerfile -t container-pulse-monitor:latest .
  docker build -f dashboard/Dockerfile -t container-pulse-dashboard:latest .

  kubectl apply -f k8s/flask-app-deployment.yml
  kubectl apply -f k8s/nginx-deployment.yml
  kubectl apply -f k8s/monitor-deployment.yml
  kubectl apply -f k8s/dashboard-deployment.yml

  echo '=== Container-Pulse is running on Kubernetes via Minikube ==='
  kubectl get pods
"

# ── Also run Docker Compose stack for Prometheus + Grafana ───────
sudo -u ubuntu bash -c "
  cd /home/ubuntu/container-pulse
  cp .env.example .env
  docker compose up -d prometheus grafana
"

echo "=== Bootstrap complete ==="
