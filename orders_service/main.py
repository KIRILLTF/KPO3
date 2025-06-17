# orders_service/main.py

import json
from datetime import datetime

from fastapi import FastAPI, Header, HTTPException
from sqlalchemy import insert, select

from database import database
from models import metadata, orders, outbox  # outbox — ваша таблица outbox
from schemas import OrderCreate, Order       # pydantic-схемы

app = FastAPI()


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/orders", response_model=Order)
async def create_order(
    order: OrderCreate,
    x_user_id: int = Header(..., alias="X-User-Id")
):
    # 1) создаём запись в orders
    query_order = insert(orders).values(
        user_id=x_user_id,
        amount=order.amount,
        description=order.description,
        status="NEW",
        created_at=datetime.utcnow(),
    )
    order_id = await database.execute(query_order)

    # 2) пишем событие в outbox (with event_type!)
    query_outbox = insert(outbox).values(
        aggregate_id=order_id,
        event_type="order_created",   # ← ОБЯЗАТЕЛЬНОЕ поле
        payload=json.dumps({
            "order_id": order_id,
            "user_id": x_user_id,
            "amount": order.amount,
            "description": order.description,
        }),
        created_at=datetime.utcnow(),
    )
    await database.execute(query_outbox)

    # 3) возвращаем клиенту
    return Order(
        id=order_id,
        user_id=x_user_id,
        amount=order.amount,
        description=order.description,
        status="NEW",
    )
