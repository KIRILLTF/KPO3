# Payments Service

## Как запустить

1. Скопируйте `.env.example` → `.env`  
2. `docker build -t payments-service .`  
3. `docker run -d --name payments-service --env-file .env -p 8002:8002 payments-service`
