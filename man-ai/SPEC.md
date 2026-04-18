# 漫AI - 动漫创作Token平台 SPEC.md

> 基于 PRD v2.1（2026-04-11）
> 项目路径：/home/wj/workspace/man-ai/

---

## 一、技术栈确认

| 组件 | 选型 | 状态 |
|------|------|------|
| 前端 | Next.js 14 | ✅ |
| 后端 | FastAPI 0.110+ | ✅ |
| 任务队列 | Celery + Redis | ✅ |
| 数据库 | PostgreSQL / MySQL | ⚠️ 待确认 |
| 存储 | MinIO / OSS | ✅ |
| AI 上游 | 硅基流动 + Wan2.1 | ⚠️ GPU未到位 |
| 入口 | Kong API Gateway | 后期 |

---

## 二、⚠️ Phase 0 待确认问题（必须回答后才能进 Phase 2）

### Q1：AI 上游先用哪个？
- **A.** 硅基流动（API，明 天就能跑通）
- **B.** 硅基流动 + Wan2.1（GPU 服务器到位后加）
- **C.** 等 GPU 服务器到位

### Q2：MVP 最核心功能？（选1个，其他先不做）
- **A.** 用户注册 + Token 余额 + AI 生成（充钱→生成→扣余额，最简闭环）
- **B.** 先只做 AI 生成（不需要登录，提示词→视频）
- **C.** 先只做套餐展示 + 支付接入

### Q3：数据库？
- **A.** PostgreSQL（全新）
- **B.** MySQL（复用 ERP）

---

## 三、MVP 范围（Phase 1-2，基于 PRD v2.1）

### 3.1 功能优先级（按 PRD Day 3-5）

| 优先级 | 功能 | 说明 |
|--------|------|------|
| P0 | 硅基流动 API 集成 | 调用 Vidu/可灵 生成视频 |
| P0 | 用户 Token 余额管理 | 扣费逻辑 |
| P1 | 套餐购买 | 年卡¥9999 等 |
| P1 | 创作工作室 /studio | 三种模式选择 |
| P2 | 支付接入 | 支付宝/微信（后期） |
| P2 | 作品广场 /gallery | 后期 |

### 3.2 API 路由设计

```
POST /api/video/generate
  Body: { prompt, mode, user_id? }
  Response: { task_id, status }

GET  /api/video/status/{task_id}
  Response: { status, video_url?, error? }

POST /api/user/register
POST /api/user/login
GET  /api/user/balance

GET  /api/packages
POST /api/order/create
```

### 3.3 核心数据模型

```python
# User
id, username, token_balance, created_at

# VideoTask
id, user_id, prompt, mode, status, video_url, token_cost, created_at

# Package
id, name, price, duration_minutes, token_amount
```

### 3.4 项目目录

```
man-ai/
├── backend/
│   ├── main.py           # FastAPI 入口
│   ├── routers/
│   │   ├── video.py      # /api/video/*
│   │   ├── user.py       # /api/user/*
│   │   └── package.py    # /api/packages/*
│   ├── services/
│   │   ├── router.py     # SmartRouter 智能路由
│   │   └── siliconflow.py # 硅基流动客户端
│   ├── models/           # Pydantic 模型
│   └── worker.py         # Celery worker
├── frontend/
│   └── (Next.js 14)
├── gan-harness/
│   ├── sprint-contract-manai-mvp.md
│   └── SPEC.md
└── README.md
```

---

## 四、已验证可工作的配置

- 硅基流动 API Key：已配置（backend/workers/video.py 已有）
- 视频存储：本地 /tmp 或 MinIO
- 路由：POST /api/video/generate → Celery → 硅基流动回调

---

## 五、依赖文档

- PRD：/home/wj/obidb/openclaw/AI工具/漫AI_PRD_v2.1.md
- 硅基流动接入：backend/workers/video.py
