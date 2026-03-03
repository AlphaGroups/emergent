from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    MONGO_URL: str
    DB_NAME: str
    CORS_ORIGINS: str = "*"
    
    CASHFREE_CLIENT_ID: str
    CASHFREE_CLIENT_SECRET: str
    CASHFREE_ENVIRONMENT: str = "sandbox"
    CASHFREE_API_BASE_URL: str = "https://payout-api.cashfree.com/payout/v1.2"
    
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()