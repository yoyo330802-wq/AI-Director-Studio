# FastAPI 应用入口

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db, close_db
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.generate import router as generate_router
from app.api.websocket import router as websocket_router
from app.api.payment import router as payment_router
from app.api.billing import router as billing_router
from app.api.moderation import router as moderation_router
from app.api.packages import router as packages_router
from app.api.hermes import router as hermes_router
from app.api.feishu_bot import router as feishu_router
from app.services.cache import cache_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动
    await init_db()
    
    # 启动Redis缓存 (Sprint 5: S5-F1)
    if settings.REDIS_CACHE_ENABLED:
        await cache_service.connect()
    
    yield
    
    # 关闭
    await cache_service.disconnect()
    await close_db()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="漫AI - 动漫创作Token平台 API\n\n提供视频生成、内容审核、支付结算、套餐管理等完整功能。",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(generate_router)
app.include_router(websocket_router)
app.include_router(payment_router, prefix="/api/v1/payment")
app.include_router(billing_router)  # Sprint 6: S6-1 按需计费API
app.include_router(moderation_router)
app.include_router(packages_router)  # Sprint 5: S5-F3 套餐API
app.include_router(hermes_router)  # Hermes多Agent协作编排
app.include_router(feishu_router)  # 飞书机器人 (Sprint 9)


@app.get("/api/v1/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "version": settings.VERSION}


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "docs": "/docs"
    }
