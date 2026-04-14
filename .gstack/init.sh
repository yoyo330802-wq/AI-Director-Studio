#!/bin/bash
# init.sh - 漫AI 环境初始化
# 返回 0 表示环境正常

set -e

PROJECT_DIR="/home/wj/workspace/manai"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

echo "🔧 初始化漫AI开发环境..."

# === Backend 检查 ===
echo "📦 检查 Python 依赖..."
python3 -c "import fastapi, sqlmodel, asyncpg, redis, celery" 2>/dev/null || {
    echo "❌ 缺少 Python 依赖"
    echo "安装: pip install -r $BACKEND_DIR/requirements.txt"
    exit 1
}

# === Frontend 检查 ===
echo "📦 检查 Node.js 依赖..."
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo "⚠️  前端依赖未安装，运行: cd $FRONTEND_DIR && npm install"
fi

# === Docker 服务检查 ===
echo "🐳 检查 Docker 服务..."
docker info >/dev/null 2>&1 || {
    echo "⚠️  Docker 未运行，尝试启动..."
    open --background docker 2>/dev/null || true
    sleep 5
}

# === 启动 docker-compose ===
if [ -f "$PROJECT_DIR/deployment/docker-compose.yml" ]; then
    echo "🔄 启动 docker-compose 服务..."
    cd "$PROJECT_DIR/deployment"
    docker-compose up -d postgres redis minio 2>/dev/null || docker-compose up -d 2>/dev/null || true

    echo "⏳ 等待数据库..."
    for i in $(seq 1 30); do
        PGPASSWORD=manai123 psql -h localhost -U manai -d manai -c "SELECT 1" >/dev/null 2>&1 && break
        sleep 1
    done
fi

# === 验证后端 ===
echo "🔍 验证后端服务..."
cd "$BACKEND_DIR"
if curl -s http://localhost:8000/api/v1/health 2>/dev/null | grep -q "ok"; then
    echo "✅ 后端服务就绪: http://localhost:8000"
else
    echo "⚠️  后端未就绪，启动: cd $BACKEND_DIR && uvicorn app.main:app --reload"
fi

# === 验证前端 ===
if [ -d "$FRONTEND_DIR/.next" ]; then
    echo "✅ 前端已构建"
else
    echo "⚠️  前端未构建，运行: cd $FRONTEND_DIR && npm run build"
fi

echo ""
echo "✅ 环境初始化完成"
echo ""
echo "📝 下一步:"
echo "  后端: cd $BACKEND_DIR && uvicorn app.main:app --reload --port 8000"
echo "  前端: cd $FRONTEND_DIR && npm run dev"
echo "  Celery: cd $BACKEND_DIR && celery -A app.tasks.celery_app worker --loglevel=info"
exit 0
