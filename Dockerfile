FROM python:3.12-alpine

WORKDIR /app

RUN apk add --no-cache curl ca-certificates

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Data persists via Docker volume
VOLUME /app/data
RUN mkdir -p /app/data

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:80/ || exit 1

CMD ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "80", "--workers", "1", "--timeout-keep-alive", "75"]
