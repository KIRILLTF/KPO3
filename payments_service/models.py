from sqlalchemy import (
    Table,
    Column,
    Integer,
    Float,
    Boolean,
    JSON,
    MetaData,
)

metadata = MetaData()

accounts = Table(
    "accounts",
    metadata,
    Column("user_id", Integer, primary_key=True),
    Column("balance", Float, nullable=False, default=0.0),
)

inbox = Table(
    "inbox",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("msg_id", Integer, nullable=False, unique=True),
    Column("payload", JSON, nullable=False),
    Column("processed", Boolean, nullable=False, default=True),
)

outbox = Table(
    "outbox",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("payload", JSON, nullable=False),
    Column("processed", Boolean, nullable=False, default=False),   # ← фикc
)
