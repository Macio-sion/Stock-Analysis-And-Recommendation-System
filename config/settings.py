"""全局配置。

通过 pydantic-settings 从环境变量 / .env 文件加载配置。
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置项。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ===== 数据库 =====
    database_url: str = "postgresql://postgres:root@localhost:5432/stock_recommendation"

    # ===== Redis =====
    redis_url: str = "redis://localhost:6379/0"

    # ===== 日志 =====
    log_level: str = "INFO"

    # ===== 数据源（阶段2使用）=====
    tushare_token: str = ""
    alphaai_token: str = ""
    alphaai_endpoint: str = "https://api.alphai.io/api/news/"

    # ===== LLM（阶段5使用，本机 Ollama）=====
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "qwen2.5:7b-instruct-q4_K_M"


settings = Settings()
