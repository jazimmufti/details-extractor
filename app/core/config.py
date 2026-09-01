"""Application configuration using Pydantic Settings."""

import os
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API Keys
    YOUTUBE_API_KEY: str = Field(default="", description="YouTube Data API v3 key")
    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API key")
    GEMINI_MODEL: str = Field(default="gemini-3.6-flash", description="Gemini model name")

    # Server settings
    HOST: str = Field(default="0.0.0.0", description="Host to bind server")
    PORT: int = Field(default=8000, description="Port to bind server")
    ENVIRONMENT: str = Field(default="development", description="Execution environment")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    
    # CORS
    CORS_ORIGINS: Union[str, List[str]] = Field(default="*", description="Allowed CORS origins")

    # Meta / Instagram Messaging API Settings
    META_APP_ID: str = Field(default="", description="Meta App ID")
    META_APP_SECRET: str = Field(default="", description="Meta App Secret")
    INSTAGRAM_ACCESS_TOKEN: str = Field(default="", description="Meta User/Page Access Token with instagram_manage_messages permission")
    INSTAGRAM_ACCOUNT_ID: str = Field(default="", description="Instagram Professional/Business Account ID")
    META_GRAPH_API_VERSION: str = Field(default="v21.0", description="Meta Graph API version")

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v == "*":
                return ["*"]
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    @property
    def has_youtube_api_key(self) -> bool:
        return bool(self.YOUTUBE_API_KEY and self.YOUTUBE_API_KEY.strip())

    @property
    def has_gemini_api_key(self) -> bool:
        return bool(self.GEMINI_API_KEY and self.GEMINI_API_KEY.strip())

    @property
    def has_meta_configured(self) -> bool:
        return bool(self.INSTAGRAM_ACCESS_TOKEN and self.INSTAGRAM_ACCESS_TOKEN.strip() and self.INSTAGRAM_ACCOUNT_ID and self.INSTAGRAM_ACCOUNT_ID.strip())


settings = Settings()
