#!/bin/bash
# 漫AI - 持续开发脚本
# 每3小时自动运行，继续完成开发任务

PROJECT_DIR="/home/wj/workspace/manai"
LOG_FILE="$PROJECT_DIR/logs/dev_$(date +%Y%m%d_%H).log"

echo "========== 持续开发 $(date) ==========" >> $LOG_FILE

cd $PROJECT_DIR

# 1. 检查并安装依赖
echo "[1/5] 检查依赖..." >> $LOG_FILE

# 后端依赖
if ! pip show fastapi > /dev/null 2>&1; then
    echo "安装后端依赖..." >> $LOG_FILE
    cd backend
    pip install -r requirements.txt >> $LOG_FILE 2>&1
    cd ..
fi

# 前端依赖
if [ ! -d "frontend/node_modules" ]; then
    echo "安装前端依赖..." >> $LOG_FILE
    cd frontend
    npm install >> $LOG_FILE 2>&1
    cd ..
fi

# 2. 代码质量检查
echo "[2/5] 代码质量检查..." >> $LOG_FILE
python3 -m py_compile backend/app/*.py 2>&1 >> $LOG_FILE
if [ $? -eq 0 ]; then
    echo "✅ Python语法OK" >> $LOG_FILE
else
    echo "❌ Python语法错误" >> $LOG_FILE
fi

# 3. Git拉取最新代码
echo "[3/5] Git同步..." >> $LOG_FILE
git pull --rebase origin master >> $LOG_FILE 2>&1 || true

# 4. 运行测试
echo "[4/5] 运行测试..." >> $LOG_FILE
# 后端API测试（如果Redis可用）
if redis-cli ping > /dev/null 2>&1; then
    echo "Redis可用，测试后端..." >> $LOG_FILE
    # 简化的健康检查
    curl -s http://localhost:8000/health >> $LOG_FILE 2>&1 || echo "后端未运行" >> $LOG_FILE
else
    echo "Redis不可用，跳过后端测试" >> $LOG_FILE
fi

# 5. 待办任务检查
echo "[5/5] 待办任务..." >> $LOG_FILE
echo "TODO: 完成剩余页面 (gallery, pricing, dashboard)" >> $LOG_FILE
echo "TODO: 支付接口集成" >> $LOG_FILE
echo "TODO: 前端依赖安装" >> $LOG_FILE
echo "TODO: 数据库迁移" >> $LOG_FILE

echo "========== 开发检查完成 $(date) ==========" >> $LOG_FILE
echo "" >> $LOG_FILE
