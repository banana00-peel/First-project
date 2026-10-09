"""配置管理模块"""
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# JWT 密钥校验：占位符集合 + 最小长度（HS256 建议 ≥ 32 字符）
_JWT_SECRET_PLACEHOLDERS = {
    "change-me",
    "please-change-me",
    "changeme",
    "secret",
    "your-secret",
    "",
}
_JWT_SECRET_MIN_LENGTH = 32


class Settings(BaseSettings):
    """应用配置"""

    # 应用基本配置
    app_name: str = "Trip-AI 旅行规划平台"
    app_version: str = "0.1.0"
    debug: bool = False

    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True  # 仅本地开发热重载；容器/生产用 uvicorn 直启（无 reloader）

    # CORS
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"

    # 限流（slowapi）：生成接口每 IP 每分钟上限
    rate_limit_generate: str = "5/minute"

    # 数据库（默认 SQLite 便于本地开发；生产用 PostgreSQL）
    database_url: str = "sqlite:///./trip.db"

    # Redis（Celery 任务队列 broker）
    redis_url: str = "redis://localhost:6379/0"

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

    @field_validator("jwt_secret")
    @classmethod
    def _validate_jwt_secret(cls, v: str) -> str:
        if v.strip().lower() in _JWT_SECRET_PLACEHOLDERS or len(v) < _JWT_SECRET_MIN_LENGTH:
            raise ValueError(
                f"JWT_SECRET 未设置或过弱：请设置至少 {_JWT_SECRET_MIN_LENGTH} 字符的随机密钥，"
                f'可用 `python -c "import secrets; print(secrets.token_hex(32))"` 生成。'
            )
        return v

    # 日志与可观测性
    log_level: str = "INFO"

    # Langfuse 链路追踪（默认关闭；开启时指向 Langfuse 云或自托管实例）
    langfuse_enabled: bool = False
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, extra="ignore"
    )

    def get_cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()


def get_settings() -> Settings:
    return settings
