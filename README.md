
- **api-gateway** (порт 8000)  
  Получает запросы `/orders/*` и `/payments/*` и переадресует их на нужный сервис.

- **orders_service** (порт 8001)  
  - `POST /orders` — создаёт заказ (статус NEW) и шлёт сообщение в очередь `payment_requests`.  
  - `GET  /orders/{id}` — возвращает данные заказа.  
  - `ws://…/ws/orders/{id}` — WebSocket : клиенты подписываются на статус, и как только платеж отработает, получают пуш `{ order_id, status }`.

- **payments_service** (порт 8002)  
  - `POST /payments/accounts` — создаёт аккаунт (header `X-User-Id`).  
  - `POST /payments/accounts/{user_id}/top-up` — пополняет баланс.  
  - `GET  /payments/accounts/{user_id}` — показывает текущий баланс.  
  - Асинхронно слушает очередь `payment_requests`, списывает деньги и пишет результат в `payment_results`.

- **RabbitMQ**  
  Две очереди:  
  1. `payment_requests` (Orders → Payments)  
  2. `payment_results`  (Payments → Orders)

---

## Как запустить

1. **Клонируйте** репозиторий и зайдите в папку:
   ```bash
   git clone https://github.com/<your-username>/KPO3.git
   cd KPO3
