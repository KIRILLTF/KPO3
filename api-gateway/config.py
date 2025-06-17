from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ORDERS_SERVICE_URL: str
    PAYMENTS_SERVICE_URL: str
    GATEWAY_PORT: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
