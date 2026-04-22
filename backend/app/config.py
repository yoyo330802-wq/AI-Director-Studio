"""
漫AI - 配置文件
"""
import os
from typing import List, ClassVar
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
    
    # Redis缓存配置 (Sprint 5: S5-F1)
    REDIS_CACHE_ENABLED: bool = os.getenv("REDIS_CACHE_ENABLED", "true").lower() == "true"
    REDIS_CACHE_TTL_DEFAULT: int = int(os.getenv("REDIS_CACHE_TTL_DEFAULT", "300"))  # 5分钟
    REDIS_CACHE_TTL_SHORT: int = int(os.getenv("REDIS_CACHE_TTL_SHORT", "60"))       # 1分钟
    REDIS_CACHE_TTL_LONG: int = int(os.getenv("REDIS_CACHE_TTL_LONG", "3600"))      # 1小时
    
    # 安全 - 生产环境必须设置环境变量
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天
    
    # 验证 SECRET_KEY 是否已设置
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.SECRET_KEY:
            import warnings
            warnings.warn(
                "WARNING: SECRET_KEY is not set! "
                "Please set the SECRET_KEY environment variable for production. "
                "Using a default key is insecure and should only be used for development.",
                RuntimeWarning
            )
            # 开发环境使用临时key，但打印警告
            self.SECRET_KEY = "dev-secret-key-" + os.urandom(16).hex()
    
    # 上游API配置
    SILICONFLOW_API_KEY: str = os.getenv("SILICONFLOW_API_KEY", "")
    VIDU_API_KEY: str = os.getenv("VIDU_API_KEY", "")
    VIDU_API_BASE: str = os.getenv("VIDU_API_BASE", "https://api.vidu.cn/v1")
    
    # Wan2.1自建集群
    WAN21_BASE_URL: str = os.getenv("WAN21_BASE_URL", "http://wan21.internal.manai.com")
    WAN21_API_KEY: str = os.getenv("WAN21_API_KEY", "")

    # ComfyUI / Wan2.1
    COMFYUI_URL: str = os.getenv("COMFYUI_URL", "http://localhost:8188")
    COMFYUI_API_KEY: str = os.getenv("COMFYUI_API_KEY", "")
    WAN21_COMFYUI_URL: str = os.getenv("WAN21_COMFYUI_URL", "http://localhost:8188")
    WAN21_COMFYUI_API_KEY: str = os.getenv("WAN21_COMFYUI_API_KEY", "")
    
    # 计费配置
    PRICING: ClassVar[dict] = {
        "fast": 0.04,      # Wan2.1-1.3B
        "balanced": 0.06,   # 智能路由
        "premium": 0.09,   # Vidu/可灵
    }

    # 成本配置
    COSTS: ClassVar[dict] = {
        "wan21_1.3b": 0.012,
        "wan21_14b": 0.025,
        "vidu": 0.050,
        "kling": 0.070,
    }
    
    # OSS/CDN 配置 (Sprint 4: S4-F1)
    OSS_ACCESS_KEY_ID: str = os.getenv("OSS_ACCESS_KEY_ID", "")
    OSS_SECRET_ACCESS_KEY: str = os.getenv("OSS_SECRET_ACCESS_KEY", "")
    OSS_ENDPOINT: str = os.getenv("OSS_ENDPOINT", "")
    OSS_REGION: str = os.getenv("OSS_REGION", "")
    OSS_BUCKET: str = os.getenv("OSS_BUCKET", "manai-videos")
    OSS_CDN_DOMAIN: str = os.getenv("OSS_CDN_DOMAIN", "")
    LOCAL_UPLOAD_DIR: str = os.getenv("LOCAL_UPLOAD_DIR", "/tmp/manai-uploads")
    
    # 内容审核配置 (Sprint 4: S4-F2)
    ALIYUN_ACCESS_KEY_ID: str = os.getenv("ALIYUN_ACCESS_KEY_ID", "")
    ALIYUN_ACCESS_KEY_SECRET: str = os.getenv("ALIYUN_ACCESS_KEY_SECRET", "")
    ALIYUN_REGION: str = os.getenv("ALIYUN_REGION", "cn-shanghai")
    CONTENT_MODERATION_ENABLED: bool = os.getenv("CONTENT_MODERATION_ENABLED", "true").lower() == "true"
    
    # 限流配置 (Sprint 4: S4-F3) - Kong使用
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    RATE_LIMIT_GENERATE_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_GENERATE_PER_MINUTE", "10"))
    
    # 监控和告警配置 (Sprint 4: S4-F4)
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/manai.log")
    ALERT_WEBHOOK_URL: str = os.getenv("ALERT_WEBHOOK_URL", "")
    ALERT_ENABLED: bool = os.getenv("ALERT_ENABLED", "true").lower() == "true"
    
    # SEO 配置 (Sprint 4: S4-F5)
    SEO_SITEMAP_URL: str = os.getenv("SEO_SITEMAP_URL", "https://manai.com/sitemap.xml")
    SEO_ROBOTS_TXT_URL: str = os.getenv("SEO_ROBOTS_TXT_URL", "https://manai.com/robots.txt")

    # 飞书机器人配置 (Sprint 9: S9-F1)
    FEISHU_APP_ID: str = os.getenv("FEISHU_APP_ID", "cli_a92ee0821db8dcc4")
    FEISHU_APP_SECRET: str = os.getenv("FEISHU_APP_SECRET", "q6nCESAMiE12vi8feEubth50FLPciC1I")
    FEISHU_VERIFICATION_TOKEN: str = os.getenv("FEISHU_VERIFICATION_TOKEN", "")

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "https://manai.com",
    ]

    # 调试模式
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    class Config:
        extra = "ignore"  # 允许额外的环境变量
        env_file = ".env"
        case_sensitive = True


settings = Settings()
