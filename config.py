# config.py

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # URL вашей Postgres БД
    database_url: str = "postgresql://shop:shop@localhost:5432/shopdb"
    # AMQP-URL RabbitMQ
    amqp_url: str = "amqp://guest:guest@localhost:5672/"

    model_config = SettingsConfigDict(
        env_file=".env",          # если хотите вытягивать из .env
        env_file_encoding="utf-8",
    )


# глобальная точка доступа
settings = Settings()
