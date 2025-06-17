# Orders Service

## Как запустить

1. Скопировать `.env.example` → `.env`
2. `docker build -t orders-service .`
3. `docker run -d --name orders-service --env-file .env -p 8001:8001 orders-service`
