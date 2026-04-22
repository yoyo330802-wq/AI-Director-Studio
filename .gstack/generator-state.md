# Generator State — Iteration 002

## Project
- **Name**: 漫AI / ComfyUI Orchestrator
- **Repo**: github.com/... (TBD)
- **Location**: /home/wj/workspace/comfyui-orchestrator

## Iteration
- **Current**: Iteration 002 — Sprint 1 后端核心

## What Was Built
### Phase 2 (Iteration 001)
- User模型 + JWT/bcrypt认证
- GenerationTask模型
- 计费服务 + 智能路由服务
- ComfyUI客户端 + 硅基流动客户端
- 认证API + 用户API + 生成API + WebSocket
- Celery视频生成任务

### Phase 4 Fixes (Iteration 002)
- 修复 bcrypt 4.2+ 兼容问题（改用bcrypt直接）
- 修复 JWT SECRET_KEY 注释（提醒生产环境必须修改）
- WebSocket改为Redis pub/sub（支持多worker）
- Celery任务进度同步推送到WebSocket

## Remaining Issues
- 需接入真实ComfyUI API（当前为mock）
- 需接入真实硅基流动API（当前为mock）
- 需创建.env并设置真实SECRET_KEY
- 缺少数据库迁移（Alembic）

## Dev Server
- Backend: `cd backend && uvicorn app.main:app --reload --port 8000`
- Celery: `cd backend && celery -A app.tasks.video_generation.celery_app worker --loglevel=info`
- Redis/PostgreSQL: `docker-compose up -d` (in deployment/)
