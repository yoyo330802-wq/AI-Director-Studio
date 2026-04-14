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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动
    await init_db()
    yield
    # 关闭
    await close_db()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
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
