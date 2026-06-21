FROM python:3.10-slim
WORKDIR /app
RUN pip install fastapi uvicorn jinja2 docker kubernetes
COPY monitor/ ./monitor/
COPY dashboard/ ./dashboard/
CMD ["uvicorn", "dashboard.main:app", "--host", "0.0.0.0", "--port", "8080"]
