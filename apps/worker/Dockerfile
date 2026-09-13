FROM python:3.11-slim

WORKDIR /app

COPY requirements.lock.txt .
RUN pip install --no-cache-dir -r requirements.lock.txt

COPY . .

ENV CREWSPAN_ENVIRONMENT=production

CMD ["celery", "-A", "worker.celery_app:celery_app", "worker", "--loglevel=info", "-Q", "crewspan.default,crewspan.notifications,crewspan.scheduling,crewspan.invoicing,crewspan.webhooks,crewspan.reports"]
