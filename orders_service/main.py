# orders_service/main.py

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy import create_engine
from databases import Database

from models import metadata, orders

DATABASE_URL = "sqlite:///./orders.db"

# создаём SQLite-файл и таблицы, если их нет
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
metadata.create_all(engine)

database = Database(DATABASE_URL)
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


class OrderCreate(BaseModel):
    amount: float
    description: str


class OrderOut(BaseModel):
    id: int
    user_id: int
    amount: float
    description: str
    status: str
    created_at: datetime


@app.post("/orders", response_model=OrderOut)
async def create_order(
    body: OrderCreate,
    x_user_id: int = Header(..., alias="X-User-Id"),
):
    query = orders.insert().values(
        user_id=x_user_id,
        amount=body.amount,
        description=body.description,
        # status и created_at заполнятся по умолчанию на стороне БД
    )
    order_id = await database.execute(query)
    if not order_id:
        raise HTTPException(status_code=500, detail="Не удалось создать заказ")

    row = await database.fetch_one(
        orders.select().where(orders.c.id == order_id)
    )
    return row


@app.get("/orders/{order_id}", response_model=OrderOut)
async def get_order(
    order_id: int,
    x_user_id: int = Header(..., alias="X-User-Id"),
):
    row = await database.fetch_one(
        orders.select().where(orders.c.id == order_id)
    )
    if not row:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    if row["user_id"] != x_user_id:
        raise HTTPException(status_code=403, detail="Это не ваш заказ")
    return row


@app.get("/orders", response_model=list[OrderOut])
async def list_orders(
    x_user_id: int = Header(..., alias="X-User-Id"),
):
    rows = await database.fetch_all(
        orders.select().where(orders.c.user_id == x_user_id)
    )
    return rows
