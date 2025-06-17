import asyncio
import databases
import sqlalchemy
import uvicorn
from fastapi import FastAPI, HTTPException

from config import settings
from models import metadata, accounts, inbox, outbox   # ← относительный импорт
from worker import start_worker                                # фоновый воркер

# ---------- База данных ----------

DATABASE_URL = "sqlite+aiosqlite:///./payments.db"

database = databases.Database(DATABASE_URL)
engine = sqlalchemy.create_engine("sqlite:///payments.db")
metadata.create_all(engine)

# ---------- FastAPI ----------

app = FastAPI(title="Payments Service")


# ---------- Жизненный цикл ----------

@app.on_event("startup")
async def startup() -> None:
    await database.connect()
    # Запускаем воркер, который читает payment_requests
    asyncio.create_task(start_worker())


@app.on_event("shutdown")
async def shutdown() -> None:
    await database.disconnect()


# ---------- REST-эндпоинты ----------

@app.post("/accounts")
async def create_account(user_id: int):
    acc = await database.fetch_one(accounts.select().where(accounts.c.user_id == user_id))
    if acc:
        return acc
    await database.execute(accounts.insert().values(user_id=user_id, balance=0))
    return {"user_id": user_id, "balance": 0.0}


@app.post("/accounts/{user_id}/top-up")
async def top_up(user_id: int, amount: float):
    acc = await database.fetch_one(accounts.select().where(accounts.c.user_id == user_id))
    if not acc:
        raise HTTPException(404, detail="Account not found")

    await database.execute(
        accounts.update()
        .where(accounts.c.user_id == user_id)
        .values(balance=acc["balance"] + amount)
    )
    return {"user_id": user_id, "balance": acc["balance"] + amount}


@app.get("/accounts/{user_id}")
async def get_balance(user_id: int):
    acc = await database.fetch_one(accounts.select().where(accounts.c.user_id == user_id))
    if not acc:
        raise HTTPException(404, detail="Account not found")
    return acc


# ---------- Точка входа (при локальном запуске) ----------

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8002)
