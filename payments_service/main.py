# payments_service/main.py

from decimal import Decimal
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, condecimal
from sqlalchemy import create_engine
from databases import Database

from models import metadata, accounts

DATABASE_URL = "sqlite:///./payments.db"

# Создание таблиц в SQLite
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
metadata.create_all(engine)

# Настройка асинхронного доступа к БД
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


# --- Pydantic-схемы ---

class TopUp(BaseModel):
    # Decimal с двумя знаками после запятой
    amount: condecimal(max_digits=12, decimal_places=2)


class AccountOut(BaseModel):
    user_id: int
    balance: Decimal

    class Config:
        orm_mode = True


# --- Эндпоинты ---

@app.post("/payments/accounts", response_model=AccountOut)
async def create_account(
    x_user_id: int = Header(..., alias="X-User-Id"),
):
    existing = await database.fetch_one(
        accounts.select().where(accounts.c.user_id == x_user_id)
    )
    if existing:
        return {"user_id": x_user_id, "balance": existing["balance"]}
    # создаём с нулевым балансом
    await database.execute(
        accounts.insert().values(user_id=x_user_id, balance=Decimal("0.00"))
    )
    return {"user_id": x_user_id, "balance": Decimal("0.00")}


@app.post("/payments/accounts/{user_id}/top-up", response_model=AccountOut)
async def top_up(
    user_id: int,
    body: TopUp,
    x_user_id: int = Header(..., alias="X-User-Id"),
):
    if user_id != x_user_id:
        raise HTTPException(status_code=403, detail="Нельзя пополнить чужой счёт")

    row = await database.fetch_one(
        accounts.select().where(accounts.c.user_id == user_id)
    )
    if not row:
        raise HTTPException(status_code=404, detail="Счёт не найден")

    # body.amount уже Decimal, складываем с балансом из БД
    new_balance = row["balance"] + body.amount

    await database.execute(
        accounts.update()
        .where(accounts.c.user_id == user_id)
        .values(balance=new_balance)
    )
    return {"user_id": user_id, "balance": new_balance}


@app.get("/payments/accounts/{user_id}", response_model=AccountOut)
async def get_balance(
    user_id: int,
    x_user_id: int = Header(..., alias="X-User-Id"),
):
    if user_id != x_user_id:
        raise HTTPException(status_code=403, detail="Нельзя смотреть чужой счёт")

    row = await database.fetch_one(
        accounts.select().where(accounts.c.user_id == user_id)
    )
    if not row:
        raise HTTPException(status_code=404, detail="Счёт не найден")

    return {"user_id": user_id, "balance": row["balance"]}
