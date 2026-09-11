"""配置管理模块"""
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings(BaseSettings):
    """应用配置"""

    # 应用基本配置
    app_name: str = "Trip-AI 旅行规划平台"
    app_version: str = "0.1.0"
    debug: bool = False

    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"

    # 数据库（默认 SQLite 便于本地开发；生产用 PostgreSQL）
    database_url: str = "sqlite:///./trip.db"

    # LLM 配置（OpenAI 兼容协议，默认 DeepSeek）
    llm_model: str = "deepseek-chat"
    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com"
    llm_temperature: float = 0.7

    # 高德地图 Web服务 API key（本地 MCP 服务器通过 AMAP_MAPS_API_KEY 注入使用）
    amap_api_key: str = ""

    # Unsplash 图片服务
    unsplash_access_key: str = ""

    # JWT
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

    def get_cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()


def get_settings() -> Settings:
    return settings
