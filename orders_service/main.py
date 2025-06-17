# orders_service/main.py

import os
import json
import asyncio
from decimal import Decimal
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, condecimal, ConfigDict
from databases import Database
from sqlalchemy import (
    create_engine, MetaData, Table, Column,
    Integer, Numeric, String, DateTime, func, select
)
import aio_pika

from models import metadata, orders

DATABASE_URL = "sqlite:///./orders.db"
RABBIT_URL   = os.getenv("RABBITMQ_URL", "amqp://guest:guest@broker:5672/")

# Настройка БД
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
metadata.create_all(engine)
db = Database(DATABASE_URL)

app = FastAPI(title="Orders Service")


# Pydantic-схемы
class CreateOrder(BaseModel):
    amount: condecimal(max_digits=12, decimal_places=2)
    description: str


class OrderOut(BaseModel):
    id: int
    user_id: int
    amount: Decimal
    description: Optional[str]
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Публикуем запрос на оплату
async def publish_payment_request(order_id: int, user_id: int, amount: Decimal):
    conn = await aio_pika.connect_robust(RABBIT_URL)
    ch = await conn.channel()
    await ch.declare_queue("payment_requests", durable=True)
    await ch.default_exchange.publish(
        aio_pika.Message(
            body=json.dumps({
                "order_id": order_id,
                "user_id": user_id,
                "amount": str(amount)
            }).encode()
        ),
        routing_key="payment_requests",
    )
    await conn.close()


# Слушаем результаты оплат
async def consume_payment_results():
    conn = await aio_pika.connect_robust(RABBIT_URL)
    ch = await conn.channel()
    q = await ch.declare_queue("payment_results", durable=True)
    async with q.iterator() as it:
        async for msg in it:
            async with msg.process():
                data = json.loads(msg.body)
                await db.execute(
                    orders.update()
                    .where(orders.c.id == data["order_id"])
                    .values(status=data["status"])
                )
    await conn.close()


@app.on_event("startup")
async def startup():
    await db.connect()
    # гарантируем наличие очереди для результатов
    conn = await aio_pika.connect_robust(RABBIT_URL)
    ch = await conn.channel()
    await ch.declare_queue("payment_results", durable=True)
    await conn.close()
    # запускаем consumer
    asyncio.create_task(consume_payment_results())


@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()


@app.post("/orders", response_model=OrderOut)
async def create_order(
    payload: CreateOrder,
    x_user_id: int = Header(..., alias="X-User-Id"),
):
    order_id = await db.execute(
        orders.insert().values(
            user_id=x_user_id,
            amount=payload.amount,
            description=payload.description,
            status="NEW",
        )
    )
    await publish_payment_request(order_id, x_user_id, payload.amount)
    row = await db.fetch_one(select(orders).where(orders.c.id == order_id))
    return row


@app.get("/orders/{order_id}", response_model=OrderOut)
async def get_order(
    order_id: int,
    x_user_id: int = Header(..., alias="X-User-Id"),
):
    row = await db.fetch_one(select(orders).where(orders.c.id == order_id))
    if not row or row["user_id"] != x_user_id:
        raise HTTPException(404, "Order not found")
    return row
