# orders_service/models.py

from sqlalchemy import (
    MetaData, Table, Column,
    Integer, Numeric, String,
    DateTime, func
)

metadata = MetaData()

orders = Table(
    "orders",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, nullable=False),
    Column("amount", Numeric(12, 2), nullable=False),
    Column("description", String(255), nullable=False),
    Column("status", String(50), nullable=False, server_default="NEW"),
    # теперь БД сама подставит текущее время в created_at
    Column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    ),
)
