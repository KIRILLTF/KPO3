from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    RABBITMQ_URL: str
    PAYMENTS_SERVICE_URL: str

    class Config:
        env_file = ".env"

settings = Settings()
