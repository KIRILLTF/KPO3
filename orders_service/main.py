import asyncio, databases, sqlalchemy, uvicorn
from fastapi import FastAPI, Request, HTTPException
from config import settings
from .models import metadata, orders, outbox          # ← относительный импорт
from .worker import start_worker
from schemas import OrderCreate, Order
from publisher import start_publisher
from consumer import start_consumer

DATABASE_URL = "sqlite+aiosqlite:///./orders.db"
database = databases.Database(DATABASE_URL)
engine = sqlalchemy.create_engine("sqlite:///orders.db")
metadata.create_all(engine)

app = FastAPI(title="Orders Service")


@app.on_event("startup")
async def startup() -> None:
    await database.connect()
    # фоновая публикация/консумер
    asyncio.create_task(start_publisher())
    asyncio.create_task(start_consumer())


@app.on_event("shutdown")
async def shutdown() -> None:
    await database.disconnect()


@app.post("/orders", response_model=Order)
async def create_order(order_in: OrderCreate, request: Request):
    if "X-User-Id" not in request.headers:
        raise HTTPException(status_code=400, detail="X-User-Id header missing")

    user_id = int(request.headers["X-User-Id"])

    # 1. сохраняем заказ
    order_id = await database.execute(
        orders.insert().values(
            user_id=user_id,
            amount=order_in.amount,
            description=order_in.description,
            status="NEW",
        )
    )

    # 2. кладём сообщение в outbox (processed=False — важно!)
    await database.execute(
        outbox.insert().values(
            payload={
                "order_id": order_id,
                "user_id": user_id,
                "amount": order_in.amount,
            },
            processed=False,
        )
    )

    return Order(
        id=order_id,
        user_id=user_id,
        amount=order_in.amount,
        description=order_in.description,
        status="NEW",
    )


@app.get("/orders")
async def list_orders(request: Request):
    user_id = int(request.headers["X-User-Id"])
    rows = await database.fetch_all(orders.select().where(orders.c.user_id == user_id))
    return rows


@app.get("/orders/{order_id}", response_model=Order)
async def get_order(order_id: int, request: Request):
    user_id = int(request.headers["X-User-Id"])
    row = await database.fetch_one(
        orders.select().where(
            (orders.c.id == order_id) & (orders.c.user_id == user_id)
        )
    )
    if not row:
        raise HTTPException(404, "Order not found")
    return row


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001)
