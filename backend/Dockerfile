FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    cron \
    tzdata \
    && ln -snf /usr/share/zoneinfo/Asia/Tehran /etc/localtime && \
    echo "Asia/Tehran" > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN echo "30 07 * * * (/usr/local/bin/python /app/domain/task.py && /usr/local/bin/python /app/server/task.py && /usr/local/bin/python /app/certificate/task.py) >> /var/log/cron.log 2>&1" > /etc/cron.d/mycron && \
    chmod 0644 /etc/cron.d/mycron && \
    crontab /etc/cron.d/mycron && \
    touch /var/log/cron.log