import os
import json
import asyncio
from decimal import Decimal

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, condecimal
from databases import Database
from sqlalchemy import (
    create_engine, MetaData, Table, Column,
    Integer, Numeric, select
)
import aio_pika

# Конфиг
DATABASE_URL = "sqlite:///./payments.db"
RABBIT_URL   = os.getenv("RABBITMQ_URL", "amqp://guest:guest@broker:5672/")

# Таблица accounts
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
metadata = MetaData()
accounts = Table(
    "accounts", metadata,
    Column("user_id", Integer, primary_key=True),
    Column("balance", Numeric(12,2,asdecimal=True), nullable=False, server_default="0.00"),
)
metadata.create_all(engine)
db = Database(DATABASE_URL)

app = FastAPI(title="Payments Service")

# Pydantic-схемы
class TopUp(BaseModel):
    amount: condecimal(max_digits=12, decimal_places=2)

class AccountOut(BaseModel):
    user_id: int
    balance: Decimal

# Consumer для payment_requests
async def process_payment_requests():
    await db.connect()
    conn = await aio_pika.connect_robust(RABBIT_URL)
    ch = await conn.channel()
    q = await ch.declare_queue("payment_requests", durable=True)

    async with q.iterator() as it:
        async for msg in it:
            async with msg.process():
                data    = json.loads(msg.body)
                user_id = data["user_id"]
                amount  = Decimal(data["amount"])
                order_id= data["order_id"]

                # списываем с аккаунта
                row = await db.fetch_one(select(accounts).where(accounts.c.user_id == user_id))
                if not row:
                    # создаём счёт, если не было
                    await db.execute(accounts.insert().values(user_id=user_id, balance=0))
                    row = {"balance": Decimal("0.00")}

                new_bal = row["balance"] - amount
                status  = "FINISHED" if new_bal >= 0 else "CANCELLED"

                await db.execute(
                    accounts.update()
                    .where(accounts.c.user_id == user_id)
                    .values(balance=new_bal)
                )

                # публикуем результат
                await ch.default_exchange.publish(
                    aio_pika.Message(
                        body=json.dumps({
                            "order_id": order_id,
                            "status": status
                        }).encode()
                    ),
                    routing_key="payment_results",
                )

    await db.disconnect()
    await conn.close()

@app.on_event("startup")
async def on_startup():
    # объявляем очередь, чтобы Order Service мог сразу публиковать
    conn = await aio_pika.connect_robust(RABBIT_URL)
    ch = await conn.channel()
    await ch.declare_queue("payment_requests", durable=True)
    await conn.close()
    # запускаем listener
    asyncio.create_task(process_payment_requests())

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/payments/accounts", response_model=AccountOut)
async def create_account(x_user_id: int = Header(..., alias="X-User-Id")):
    await db.connect()
    existing = await db.fetch_one(select(accounts).where(accounts.c.user_id == x_user_id))
    if existing:
        await db.disconnect()
        return {"user_id": x_user_id, "balance": existing["balance"]}
    await db.execute(accounts.insert().values(user_id=x_user_id, balance=0))
    await db.disconnect()
    return {"user_id": x_user_id, "balance": Decimal("0.00")}

@app.post("/payments/accounts/{user_id}/top-up", response_model=AccountOut)
async def top_up(
    user_id: int,
    body: TopUp,
    x_user_id: int = Header(..., alias="X-User-Id")
):
    if user_id != x_user_id:
        raise HTTPException(403, "Forbidden")
    await db.connect()
    row = await db.fetch_one(select(accounts).where(accounts.c.user_id == user_id))
    if not row:
        await db.disconnect()
        raise HTTPException(404, "Account not found")
    new_balance = row["balance"] + body.amount
    await db.execute(
        accounts.update().where(accounts.c.user_id == user_id).values(balance=new_balance)
    )
    await db.disconnect()
    return {"user_id": user_id, "balance": new_balance}

@app.get("/payments/accounts/{user_id}", response_model=AccountOut)
async def get_balance(
    user_id: int,
    x_user_id: int = Header(..., alias="X-User-Id")
):
    if user_id != x_user_id:
        raise HTTPException(403, "Forbidden")
    await db.connect()
    row = await db.fetch_one(select(accounts).where(accounts.c.user_id == user_id))
    await db.disconnect()
    if not row:
        raise HTTPException(404, "Account not found")
    return {"user_id": user_id, "balance": row["balance"]}
