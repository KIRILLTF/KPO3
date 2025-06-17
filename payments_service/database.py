from databases import Database
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import MetaData
from config import settings

database = Database(settings.DATABASE_URL)
async_engine = create_async_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
)
metadata = MetaData()