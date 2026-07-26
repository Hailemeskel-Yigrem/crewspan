FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FIELDSPAN_ENVIRONMENT=production

CMD ["celery", "-A", "worker.celery_app:celery_app", "worker", "--loglevel=info", "-Q", "fieldspan.default,fieldspan.notifications,fieldspan.scheduling,fieldspan.invoicing,fieldspan.webhooks,fieldspan.reports"]
