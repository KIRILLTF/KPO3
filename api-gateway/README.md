# API Gateway

Проксирует запросы `/orders/*` → Orders Service и `/payments/*` → Payments Service.

## Как запустить

1. Скопировать `.env.example` → `.env` и задать реальные URL:
   ```bash
   cp .env.example .env
   # отредактировать .env: ORDERS_SERVICE_URL, PAYMENTS_SERVICE_URL
