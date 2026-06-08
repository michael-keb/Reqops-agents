FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bridge/ bridge/
COPY signals-v01/ signals-v01/
COPY ui/ ui/

ENV UPLIFT_HOST=0.0.0.0
ENV UPLIFT_PORT=8786
ENV UPLIFT_AGENT_MODE=headless
ENV UPLIFT_DISCOVERY_RUNNER=sdk
ENV UPLIFT_SIGNALS_RUNNER=sdk
ENV PYTHONUNBUFFERED=1

EXPOSE 8786

VOLUME ["/app/sessions", "/app/logs"]

CMD ["python", "-m", "bridge.server"]
