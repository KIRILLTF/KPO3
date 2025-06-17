# orders_service/models.py
import sqlalchemy as sa
import sqlalchemy.dialects.sqlite as sqlite

metadata = sa.MetaData()

orders = sa.Table(
    "orders",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("user_id", sa.Integer, nullable=False),
    sa.Column("amount", sa.Float, nullable=False),
    sa.Column("description", sa.String, nullable=True),
    sa.Column("status", sa.String, default="NEW", nullable=False),
)

outbox = sa.Table(
    "outbox",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("event_type", sa.String, nullable=False),
    sa.Column("payload", sqlite.JSON, nullable=False),
    sa.Column("processed", sa.Boolean, default=False, nullable=False),
)
