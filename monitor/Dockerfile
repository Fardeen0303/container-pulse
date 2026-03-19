FROM python:3.10
WORKDIR /app
RUN pip install docker slack-sdk prometheus-client
COPY monitor.py .
CMD ["python", "monitor.py"]
