#!/bin/bash
# 漫AI - 代码质量检查脚本
# 每3小时运行一次

PROJECT_DIR="/home/wj/workspace/manai"
LOG_FILE="/home/wj/workspace/manai/logs/quality_check.log"

echo "========== 代码质量检查 $(date) ==========" >> $LOG_FILE

# 检查Python语法
echo "检查Python语法..." >> $LOG_FILE
find $PROJECT_DIR/backend -name "*.py" -exec python3 -m py_compile {} \; 2>&1 >> $LOG_FILE
if [ $? -eq 0 ]; then
    echo "✅ Python语法检查通过" >> $LOG_FILE
else
    echo "❌ Python语法检查失败" >> $LOG_FILE
fi

# 检查TypeScript语法
echo "检查TypeScript语法..." >> $LOG_FILE
cd $PROJECT_DIR/frontend
if [ -f "package.json" ]; then
    npx tsc --noEmit 2>&1 >> $LOG_FILE || true
    echo "✅ TypeScript检查完成" >> $LOG_FILE
else
    echo "⚠️ 前端项目未初始化" >> $LOG_FILE
fi

# 检查依赖
echo "检查依赖配置..." >> $LOG_FILE
if [ -f "$PROJECT_DIR/backend/requirements.txt" ]; then
    echo "✅ 后端依赖文件存在" >> $LOG_FILE
fi
if [ -f "$PROJECT_DIR/frontend/package.json" ]; then
    echo "✅ 前端依赖文件存在" >> $LOG_FILE
fi

# 检查关键文件
echo "检查关键文件..." >> $LOG_FILE
for file in \
    "$PROJECT_DIR/backend/app/main.py" \
    "$PROJECT_DIR/backend/app/config.py" \
    "$PROJECT_DIR/backend/app/router/smart_router.py" \
    "$PROJECT_DIR/frontend/app/studio/page.tsx" \
    "$PROJECT_DIR/frontend/lib/api.ts"; do
    if [ -f "$file" ]; then
        echo "✅ $file 存在" >> $LOG_FILE
    else
        echo "❌ $file 缺失!" >> $LOG_FILE
    fi
done

# 代码行数统计
echo "代码统计:" >> $LOG_FILE
echo "  Python: $(find $PROJECT_DIR/backend -name '*.py' | xargs wc -l | tail -1)" >> $LOG_FILE
echo "  TypeScript: $(find $PROJECT_DIR/frontend -name '*.ts' -o -name '*.tsx' | xargs wc -l | tail -1)" >> $LOG_FILE

echo "========== 检查完成 $(date) ==========" >> $LOG_FILE
echo "" >> $LOG_FILE
