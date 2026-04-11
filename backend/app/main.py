"""
漫AI - 动漫创作Token平台
FastAPI 主入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import users, generate, billing
from app.config import settings

app = FastAPI(
    title="漫AI API",
    version="1.0.0",
    description="动漫创作Token平台 - 基于Wan2.1自建 + 硅基流动/Vidu商业API"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(users.router, prefix="/v1/users", tags=["用户"])
app.include_router(generate.router, prefix="/v1/generate", tags=["生成"])
app.include_router(billing.router, prefix="/v1/bill", tags=["计费"])


@app.get("/")
def root():
    """根路径"""
    return {
        "name": "漫AI API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
def health():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
