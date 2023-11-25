FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV RELAYOPS_ENVIRONMENT=production

CMD ["celery", "-A", "worker.celery_app:celery_app", "worker", "--loglevel=info", "-Q", "relayops.default,relayops.notifications,relayops.scheduling,relayops.invoicing,relayops.webhooks,relayops.reports"]
