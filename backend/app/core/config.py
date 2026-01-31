from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    CORS_ORIGINS: List[str] = Field(default_factory=list)

    PROJECT_NAME: str = "mAiL Backend"
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str = "sqlite:///./feedback.db"

    # Gmail

    TOKENS_DIR: str = "tokens"
    GOOGLE_CLIENT_ID: str = Field(..., alias="GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: str = Field(..., alias="GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI: str = Field(..., alias="GOOGLE_REDIRECT_URI")

    # LLM Keys
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openrouter_api_key: str | None = Field(default=None, alias="OPENROUTER_API_KEY")

    # Security
    SECRET_KEY: str = "supersecretkey" # TODO: Change in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440 # 24 hours
    TOKEN_ENCRYPTION_KEY: str = Field(..., description="Key for encrypting OAuth tokens")


    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"   # 🔥 avoids crashes if extra vars exist
    )

settings = Settings()