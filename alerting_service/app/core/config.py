from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    PROJECT_NAME: str = "IoT Alerting Service"
    API_V1_STR: str = "/api/v1"

    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: str = "5432"

    REDIS_HOST: str
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str | None = None
    REDIS_DB: int = 0

    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASS: str = "guest"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_VHOST: str = "/"
    RABBITMQ_EXCHANGE_NAME: str = "iot_events_exchange"
    RABBITMQ_ROUTING_KEY: str = "event.new"
    RABBITMQ_QUEUE_NAME: str = "event_processing_queue"

    # Alert thresholds
    SPEED_VIOLATION_THRESHOLD: int = 90  # km/h
    AUTHORIZED_USERS_CACHE_TTL: int = 3600  # 1 hour
    
    # Seeding configuration
    ENABLE_SEEDING: bool = True
    
    # Service-to-service communication (optional)
    INGESTION_SERVICE_URL: str | None = None

    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def ASYNC_SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def REDIS_URL(self) -> str:
        password_part = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{password_part}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def RABBITMQ_URL(self) -> str:
        return f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASS}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}{self.RABBITMQ_VHOST}"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings() 