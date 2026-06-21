FROM python:3.10-slim
WORKDIR /app
RUN pip install docker slack-sdk prometheus-client requests kubernetes
COPY monitor/ ./monitor/
CMD ["python", "-m", "monitor.monitor"]
