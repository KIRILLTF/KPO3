# payments_service/models.py

from decimal import Decimal
from sqlalchemy import (
    MetaData,
    Table,
    Column,
    Integer,
    Numeric,
    String,
    DateTime,
    func,
)
from pydantic import BaseModel, condecimal

metadata = MetaData()

# --- SQLAlchemy tables ---

accounts = Table(
    "accounts",
    metadata,
    Column("user_id", Integer, primary_key=True),
    # asdecimal=True гарантирует, что мы всегда получаем Decimal,
    # server_default задаёт начальный баланс 0.00
    Column(
        "balance",
        Numeric(12, 2, asdecimal=True),
        nullable=False,
        server_default="0.00",
    ),
)

inbox = Table(
    "inbox",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("event_id", String(255), nullable=False),
    Column("payload", String, nullable=False),
    Column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    ),
)

outbox = Table(
    "outbox",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("aggregate_id", Integer, nullable=False),
    Column("event_type", String(255), nullable=False),
    Column("payload", String, nullable=False),
    Column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    ),
)

# --- Pydantic-схемы ---

class TopUpRequest(BaseModel):
    # Decimal с двумя знаками после точки
    amount: condecimal(max_digits=12, decimal_places=2)

class AccountResponse(BaseModel):
    user_id: int
    balance: Decimal

    class Config:
        orm_mode = True
