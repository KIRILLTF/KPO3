# KPO3 — простой интернет-магазин на микросервисах

Это мой учебный проект: два бэкенд-сервиса (Orders и Payments) и API-шлюз.

---

##

* **api-gateway** (порт 8000)
  Прокси:

  * `/orders/*` → Orders Service
  * `/payments/*` → Payments Service

* **orders\_service** (порт 8001)

  * `POST /orders` — создаёт заказ (статус NEW) и шлёт `payment_requests` в RabbitMQ
  * `GET  /orders/{id}` — возвращает данные заказа
  * `ws://…/ws/orders/{id}` — WebSocket: подписка на смену статуса

* **payments\_service** (порт 8002)

  * `POST /payments/accounts`                     — создать счёт (header `X-User-Id`)
  * `POST /payments/accounts/{user_id}/top-up`    — пополнить баланс
  * `GET  /payments/accounts/{user_id}`           — посмотреть баланс
  * Слушает `payment_requests`, списывает деньги и публикует `payment_results`

* **RabbitMQ**

  * `payment_requests` (Orders → Payments)
  * `payment_results`  (Payments → Orders)

---

## Быстрый старт

1. 

   ```bash
   git clone https://github.com/<ваш-ник>/KPO3.git
   cd KPO3
   ```

3. **Запуск**:

   ```bash
   docker compose down -v
   docker compose up --build -d
   ```

4. **Swagger**:

   * API Gateway:    [http://localhost:8000/docs](http://localhost:8000/docs)
   * Orders Service: [http://localhost:8001/docs](http://localhost:8001/docs)
   * Payments Svс:   [http://localhost:8002/docs](http://localhost:8002/docs)

---

## Проверка

1. **Создать счёт**

   * Header: `X-User-Id: 42`
   * `POST http://localhost:8002/payments/accounts`

2. **Пополнить баланс**

   * `POST http://localhost:8002/payments/accounts/42/top-up`

     ```json
     { "amount": 1000.00 }
     ```

3. **Оформить заказ**

   * Header: `X-User-Id: 42`
   * `POST http://localhost:8001/orders`

     ```json
     { "amount": 250.00, "description": "Мой первый заказ" }
     ```

4. **Подписаться на WebSocket**

   * `ws://localhost:8001/ws/orders/{order_id}`
     При изменении статуса придёт сообщение:

   ```json
   { "order_id": 123, "status": "FINISHED" }
   ```



Автор: Зайцев Кирилл Николаевич
