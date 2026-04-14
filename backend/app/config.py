"""
漫AI - 配置文件
"""
import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # 应用信息
    APP_NAME: str = "漫AI - 动漫创作Token平台"
    VERSION: str = "0.1.0"

    # 数据库
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://manai:manai123@localhost:5432/manai"
    )
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # 安全
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", 
        "manai-secret-key-change-in-production-2026"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天
    
    # 上游API配置
    SILICONFLOW_API_KEY: str = os.getenv("SILICONFLOW_API_KEY", "")
    VIDU_API_KEY: str = os.getenv("VIDU_API_KEY", "")
    VIDU_API_BASE: str = os.getenv("VIDU_API_BASE", "https://api.vidu.cn/v1")
    
    # Wan2.1自建集群
    WAN21_BASE_URL: str = os.getenv("WAN21_BASE_URL", "http://wan21.internal.manai.com")
    WAN21_API_KEY: str = os.getenv("WAN21_API_KEY", "")
    
    # 计费配置
    PRICING = {
        "fast": 0.04,      # Wan2.1-1.3B
        "balanced": 0.06,   # 智能路由
        "premium": 0.09,   # Vidu/可灵
    }
    
    # 成本配置
    COSTS = {
        "wan21_1.3b": 0.012,
        "wan21_14b": 0.025,
        "vidu": 0.050,
        "kling": 0.070,
    }
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
