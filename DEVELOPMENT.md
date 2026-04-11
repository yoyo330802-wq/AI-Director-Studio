# 漫AI平台开发任务

## 项目概述
基于Wan2.1自建 + 硅基流动/Vidu商业API的动漫视频生成平台

## 技术栈
- 前端: Next.js 14 + TypeScript + TailwindCSS + Framer Motion
- 后端: FastAPI 0.110+ + Python 3.11+
- 数据库: PostgreSQL + MongoDB + Redis
- 任务队列: Celery + Redis
- 存储: MinIO/OSS

## 项目结构
```
/home/wj/workspace/manai/
├── frontend/           # Next.js前端
│   ├── app/
│   │   ├── studio/    # 创作工作室
│   │   ├── gallery/   # 作品广场
│   │   ├── templates/ # 提示词模板
│   │   ├── pricing/   # 套餐购买
│   │   ├── dashboard/ # 用户中心
│   │   └── api-docs/ # API文档
│   └── package.json
├── backend/            # FastAPI后端
│   ├── app/
│   │   ├── api/      # API路由
│   │   ├── clients/  # 上游客户端
│   │   ├── router/   # 智能路由
│   │   ├── services/ # 业务服务
│   │   ├── models/   # 数据模型
│   │   └── tasks/    # Celery任务
│   └── requirements.txt
├── deployment/        # 部署配置
└── docs/             # 文档
```

## 开发任务清单

### 阶段1: 项目初始化
1. 初始化Next.js 14项目
2. 初始化FastAPI项目
3. 配置数据库连接
4. 配置环境变量

### 阶段2: 后端核心
1. 用户认证系统 (JWT)
2. 智能路由引擎 (SmartRouter)
3. Wan2.1客户端
4. 硅基流动客户端
5. Vidu客户端
6. 计费服务
7. Celery任务队列

### 阶段3: 前端核心
1. 创作工作室页面
2. 模式选择组件
3. 提示词输入组件
4. 文件上传组件
5. 实时进度显示
6. 用户中心
7. 套餐购买页面

### 阶段4: 支付集成
1. 支付宝/微信支付接入
2. 订单管理系统
3. 余额扣减逻辑

### 阶段5: 测试与部署
1. API测试
2. 前端测试
3. 部署脚本

## 执行要求
- 完整实现所有功能
- 确保代码质量
- 定期提交代码
