
from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    APP_NAME: str = "Production AI SaaS Backend"
    APP_ENV: str = "development"
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite:///./app.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    LLM_API_KEY: str = ""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    JWT_SECRET_KEY:str
    JWT_ALGORITHM:str="HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES:int=30
    GEMINI_API_KEY:str=""
    GEMINI_MODEL:str="gemini-3.8-flash"
    REDIS_URL:str
    AI_REQUESTS_PER_MINUTE: int = 20
    AI_REQUESTS_PER_DAY: int = 100
    AI_MAX_INPUT_CHARS: int = 12000
    AI_MAX_OUTPUT_TOKENS: int = 1024
    AI_DAILY_TOKEN_LIMIT: int = 100000
settings = Settings()
