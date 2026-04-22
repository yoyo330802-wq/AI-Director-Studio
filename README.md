# 漫AI - 动漫创作Token平台

> **比官网便宜30%，国产动漫创作首选AI视频平台**

基于 Wan2.1（自建部署）+ 硅基流动/Vidu（商业API）混合架构的动漫视频生成平台。

## 🎯 产品特点

- **成本优势**: 比官方定价便宜30-40%
- **智能路由**: 自动选择最优生成渠道
- **动漫优化**: 专为动漫风格优化的模型
- **高可用**: 多渠道容灾，SLA 99.5%

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────┐
│                 CDN 层                       │
│           (CloudFlare/七牛云)                │
└─────────────────────┬───────────────────────┘
                      ↓
┌─────────────────────────────────────────────┐
│                 前端 (Next.js 14)            │
│  /studio  /gallery  /templates  /pricing    │
└─────────────────────┬───────────────────────┘
                      ↓
┌─────────────────────────────────────────────┐
│              网关层 (Nginx)                  │
│           认证 / 限流 / 缓存                  │
└─────────────────────┬───────────────────────┘
                      ↓
┌─────────────────────────────────────────────┐
│              后端 (FastAPI)                  │
│  用户服务 | 智能路由 | 计费服务 | 任务队列    │
└─────────────────────┬───────────────────────┘
                      ↓
┌──────────┬──────────┬──────────┐
│ Wan2.1   │ 硅基流动  │  Vidu    │
│ (自建)   │ (API代理) │ (动漫优化)│
└──────────┴──────────┴──────────┘
```

## 💻 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Next.js 14, TypeScript, TailwindCSS, Framer Motion |
| 后端 | FastAPI, Python 3.11, Celery |
| 数据库 | PostgreSQL, Redis, MongoDB |
| 上游 | Wan2.1 (自建), 硅基流动, Vidu |

## 🚀 快速开始

### 前置要求

- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+
- Python 3.11+

### 安装

```bash
# 克隆项目
git clone https://github.com/your-repo/manai.git
cd manai

# 配置环境变量
cp deployment/.env.example deployment/.env
# 编辑 .env 填入你的API密钥

# 启动服务
docker-compose -f deployment/docker-compose.yml up -d
```

### 开发模式

```bash
# 后端
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# 前端
cd frontend
npm install
npm run dev
```

## 📁 项目结构

```
manai/
├── frontend/                 # Next.js 前端
│   ├── app/                  # App Router
│   │   ├── studio/          # 创作工作室
│   │   └── ...
│   ├── lib/                 # 工具函数
│   └── package.json
├── backend/                  # FastAPI 后端
│   ├── app/
│   │   ├── api/             # API路由
│   │   ├── clients/         # 上游客户端
│   │   ├── router/          # 智能路由
│   │   ├── services/        # 业务服务
│   │   ├── tasks/           # Celery任务
│   │   └── models/          # 数据模型
│   └── requirements.txt
├── deployment/               # 部署配置
│   ├── docker-compose.yml
│   └── nginx.conf
└── README.md
```

## 🎨 生成模式

| 模式 | 模型 | 价格 | 速度 | 适用场景 |
|------|------|------|------|---------|
| 闪电模式 | Wan2.1-1.3B | ¥0.04/秒 | ~15秒 | 快速验证 |
| 智能模式 | 智能路由 | ¥0.06/秒 | ~30秒 | 日常创作 |
| 专业模式 | Vidu/可灵 | ¥0.09/秒 | ~60秒 | 商用级质量 |

## 💰 定价

### 按量付费

| 模型 | 成本 | 售价 | 官网价 |
|------|------|------|-------|
| Wan2.1-14B(自建) | ¥0.025/秒 | ¥0.07/秒 | - |
| Wan2.1-1.3B(自建) | ¥0.012/秒 | ¥0.04/秒 | - |
| Vidu | ¥0.050/秒 | ¥0.08/秒 | ¥0.10/秒 |
| 可灵 | ¥0.070/秒 | ¥0.09/秒 | ¥0.10/秒 |

### 套餐

| 套餐 | 价格 | 时长 | 折扣 |
|------|------|------|------|
| 体验包 | ¥39 | 10分钟 | 65折 |
| 创作者月卡 | ¥399 | 100分钟 | 66折 |
| 工作室季卡 | ¥1799 | 500分钟/月 | 60折 |
| 企业年卡 | ¥9999 | 3000分钟/月 | - |

## 🔧 开发指南

### 添加新的上游渠道

1. 在 `backend/app/clients/` 创建新的客户端
2. 在 `backend/app/router/smart_router.py` 添加渠道配置
3. 更新 `backend/app/config.py` 中的定价配置

### API 文档

启动后访问: http://localhost:8000/docs

## 📝 许可证

MIT License

## 🤝 联系方式

- 邮箱: support@manai.com
- 微信: manai_support
