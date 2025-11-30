import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # RabbitMQ Configuration
    rabbitmq_host: str = os.getenv("RABBITMQ_HOST", "localhost")
    rabbitmq_port: int = int(os.getenv("RABBITMQ_PORT", 5672))
    rabbitmq_user: str = os.getenv("RABBITMQ_USER", "guest")
    rabbitmq_password: str = os.getenv("RABBITMQ_PASSWORD", "guest")
    rabbitmq_vhost: str = os.getenv("RABBITMQ_VHOST", "/")
    
    # Service Configuration
    service_port: int = int(os.getenv("NOTIFICATION_SERVICE_PORT", 8000))
    service_host: str = os.getenv("NOTIFICATION_SERVICE_HOST", "0.0.0.0")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # MongoDB Configuration
    mongodb_uri: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    mongodb_db: str = os.getenv("MONGODB_DB", "notifications")
    
    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")
    
    @property
    def rabbitmq_url(self) -> str:
        return f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}@{self.rabbitmq_host}:{self.rabbitmq_port}{self.rabbitmq_vhost}"
    
    class Config:
        env_file = ".env"

settings = Settings()
