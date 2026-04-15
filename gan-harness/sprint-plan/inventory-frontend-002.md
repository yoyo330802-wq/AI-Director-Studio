# 漫AI 前端页面清单 (Inventory)

> 盘点时间: 2026-04-15
> 项目路径: `/home/wj/workspace/manai/frontend/`
> 技术栈: Next.js 14 + TypeScript + Tailwind CSS + Zustand + React Query

---

## 概览

| 页面 | 路由 | 文件路径 | 功能模块 |
|------|------|----------|----------|
| 首页 | `/` | `app/page.tsx` | 入口页(跳转至studio) |
| 创作工作室 | `/studio` | `app/studio/page.tsx` | AI视频生成核心 |
| 用户中心 | `/dashboard` | `app/dashboard/page.tsx` | 用户信息管理 |
| 模板广场 | `/templates` | `app/templates/page.tsx` | 提示词模板库 |
| API文档 | `/api-docs` | `app/api-docs/page.tsx` | 开发者API文档 |
| 定价 | `/pricing` | `app/pricing/page.tsx` | 套餐购买 |
| 作品广场 | `/gallery` | `app/gallery/page.tsx` | 社区作品展示 |
| 管理后台 | `/admin` | `app/admin/page.tsx` | 平台运营管理 |

---

## 页面详情

### 1. 首页 (`/`)

**文件**: `app/page.tsx`

**功能描述**:
- 展示漫AI品牌标语: "动漫创作Token平台 - 比官网便宜30%"
- 提供"立即开始创作"按钮
- 自动重定向到 `/studio`

**主要组件**: 无 (纯跳转页)

**依赖状态**: 无

---

### 2. 创作工作室 (`/studio`)

**文件**: `app/studio/page.tsx`

**功能描述**:
- AI视频生成核心页面
- 提供三种生成模式: 闪电模式(fast)、智能模式(balanced)、专业模式(premium)
- 提示词输入 (最多500字符)
- 负向提示词输入
- 视频时长选择: 5秒/10秒
- 宽高比选择: 16:9(横屏)、9:16(竖屏)、1:1(方形)
- 参考图片上传
- 预估成本计算
- 路由预览 (显示通道名称、预计等待时间、质量评分)
- 任务状态实时显示
- 任务历史记录

**主要组件**:
- `MODES` - 生成模式配置对象
- 模式选择卡片
- 提示词输入区
- 参数设置区
- 参考图上传区
- 生成按钮
- 当前任务状态面板
- 任务历史面板

**API调用**:
- `GET /v1/users/me` - 获取用户信息
- `POST /v1/generate` - 创建生成任务
- `GET /v1/generate/route/preview` - 路由预览

**状态管理** (`lib/store.ts`):
- `user`, `isAuthenticated`
- `currentTask`, `isGenerating`

---

### 3. 用户中心 (`/dashboard`)

**文件**: `app/dashboard/page.tsx`

**功能描述**:
- 用户个人信息中心
- 左侧导航菜单 (6个模块)
- 深色主题界面

**子模块**:

| 模块ID | 名称 | 功能 |
|--------|------|------|
| `overview` | 概览 | 统计卡片(余额/额度/消费)、最近任务、VIP推广 |
| `videos` | 我的作品 | 作品列表 (开发中) |
| `orders` | 订单记录 | 订单列表展示 |
| `wallet` | 钱包 | 余额卡片、充值、额度进度条 |
| `subscription` | 会员 | VIP状态展示、VIP特权说明 |
| `settings` | 设置 | 用户名修改、API Key复制、通知设置 |

**API调用**:
- `GET /v1/users/me` - 获取用户信息
- `GET /v1/tasks?page=1&page_size=5` - 任务列表
- `GET /v1/orders?page=1&page_size=5` - 订单列表

**用户等级系统**:
- `L1_TRIAL` - 体验版
- `L2_CREATOR` - 创作者
- `L3_STUDIO` - 工作室
- `L4_ENTERPRISE` - 企业版

---

### 4. 模板广场 (`/templates`)

**文件**: `app/templates/page.tsx`

**功能描述**:
- 提示词模板库
- 分类筛选 (全部/动漫风格/3D渲染/写实/抽象艺术/音乐视频/商业广告)
- 关键词搜索
- 网格/列表两种视图模式
- 模板收藏功能
- 一键复制提示词
- 使用模板跳转到Studio

**模板数据结构**:
```typescript
interface Template {
  id: number
  name: string
  description: string
  category: string
  prompt_template: string
  negative_prompt_template: string | null
  recommended_mode: string | null
  recommended_duration: number | null
  tags: string[]
  usage_count: number
  is_official: boolean
  cover_image: string
  demo_video: string | null
}
```

**API调用**:
- `GET /v1/templates?category=xxx` - 获取模板列表

---

### 5. API文档 (`/api-docs`)

**文件**: `app/api-docs/page.tsx`

**功能描述**:
- 漫AI开发者中心
- API端点分类展示
- 端点详情展开 (参数表格、请求/响应示例)
- 代码复制功能
- 在线调试按钮 (UI占位)
- 搜索功能

**API分类**:
| 分类ID | 名称 | 端点数量 |
|--------|------|----------|
| `auth` | 认证 | 2 |
| `users` | 用户 | 1 |
| `generation` | 视频生成 | 1 |
| `tasks` | 任务管理 | 2 |
| `videos` | 作品管理 | 2 |
| `payments` | 支付 | 2 |

**主要端点**:
- `POST /v1/auth/register` - 用户注册
- `POST /v1/auth/login` - 用户登录
- `POST /v1/generations` - 创建生成任务
- `GET /v1/tasks/{task_id}` - 获取任务状态
- `GET /v1/tasks` - 任务列表
- `GET /v1/users/me` - 获取当前用户
- `GET /v1/videos` - 作品列表
- `GET /v1/videos/{id}` - 作品详情
- `GET /v1/payments/packages` - 套餐列表
- `POST /v1/payments/create` - 创建订单

---

### 6. 定价 (`/pricing`)

**文件**: `app/pricing/page.tsx`

**功能描述**:
- 套餐方案展示
- 月付/年付切换 (年付8折)
- 4档套餐:

| 套餐 | Level | 价格 | 额度 |
|------|-------|------|------|
| 体验版 | `L1_TRIAL` | 免费 | 5分钟 |
| 创作者 | `L2_CREATOR` | ¥39/月 | 60分钟 |
| 工作室 | `L3_STUDIO` | ¥199/月 | 300分钟 |
| 企业版 | `L4_ENTERPRISE` | ¥9999/年 | 无限 |

**功能特权**:
- 优先队列
- 无水印下载
- API访问权限
- 批量生成
- 专属客服
- 4K输出 (企业版)
- 专属GPU通道 (企业版)

**FAQ区域**: 额度用完、退款、API权限、支付方式

**API调用**:
- `GET /v1/payments/packages` - 获取套餐列表
- `POST /v1/payments/create` - 创建订单

---

### 7. 作品广场 (`/gallery`)

**文件**: `app/gallery/page.tsx`

**功能描述**:
- 社区作品展示
- 分类筛选 (全部/动漫/3D/写实/抽象/音乐)
- 排序选项 (最新/最热/趋势)
- 关键词搜索
- 网格/列表两种视图模式
- 视频详情弹窗播放
- 点赞、分享功能
- 播放量/点赞数/发布时间展示

**视频数据结构**:
```typescript
interface Video {
  id: number
  title: string
  description: string
  video_url: string
  cover_url: string
  thumbnail_url: string
  duration: number
  width: number
  height: number
  view_count: number
  like_count: number
  share_count: number
  is_featured: boolean
  is_ai_recommended: boolean
  tags: string[]
  category: string
  created_at: string
  user: { id, username, nickname, avatar }
}
```

**API调用**:
- `GET /v1/videos?page=1&page_size=20&sort=latest&category=xxx` - 获取视频列表
- `POST /v1/videos/{id}/like` - 点赞

---

### 8. 管理后台 (`/admin`)

**文件**: `app/admin/page.tsx`

**功能描述**:
- 平台运营管理系统
- 左侧导航 (6个模块)

**子模块**:

| 模块ID | 名称 | 功能状态 |
|--------|------|----------|
| `dashboard` | 仪表盘 | 统计卡片(用户/作品/订单/收入)、收入趋势图表(占位)、用户增长图表(占位)、最近订单列表 |
| `users` | 用户管理 | 用户表格(导出/刷新)、搜索、等级/余额/状态显示 |
| `videos` | 作品管理 | 占位 "作品管理功能开发中..." |
| `orders` | 订单管理 | 占位 "订单管理功能开发中..." |
| `channels` | 渠道管理 | GPU通道状态卡片 (Wan2.1-14B/1.3B, Vidu, 可灵) - 请求数/成功率/平均耗时 |
| `system` | 系统设置 | 开关配置 (用户注册/邮箱验证/内容审核) |

**系统信息**: v3.0.0

**API调用**:
- `GET /v1/admin/stats` - 获取管理统计数据

---

## 共享组件/库

### 状态管理 (`lib/store.ts`)
使用 Zustand + persist middleware

**状态结构**:
- `user: User | null`
- `token: string | null`
- `isAuthenticated: boolean`
- `generation: GenerationState`
- `currentTask: Task | null`
- `tasks: Task[]`
- `isGenerating: boolean`
- `showBalanceModal: boolean`

### API客户端 (`lib/api.ts`)
使用 Axios 封装

**主要方法**:
- `register(name, email, password)`
- `login(email, password)`
- `logout()`
- `getCurrentUser()`
- `createTask(params)` → `POST /v1/generate`
- `getTaskStatus(taskId)` → `GET /v1/generate/{taskId}`
- `previewRoute(mode, duration)` → `GET /v1/generate/route/preview`
- `recharge(amount, paymentMethod)`
- `getTransactions(limit)`
- `getPackages()`

### 工具函数 (`lib/utils.ts`)
- `cn()` - className合并 (clsx + tailwind-merge)
- `formatCurrency()` - 货币格式化

---

## 路由结构

```
app/
├── page.tsx                    # / (首页，重定向到/studio)
├── layout.tsx                  # 根布局
├── providers.tsx               # React Query Provider
├── studio/
│   └── page.tsx                # /studio (创作工作室)
├── dashboard/
│   └── page.tsx                # /dashboard (用户中心)
├── templates/
│   └── page.tsx                # /templates (模板广场)
├── api-docs/
│   └── page.tsx                # /api-docs (API文档)
├── pricing/
│   └── page.tsx                # /pricing (定价)
├── gallery/
│   └── page.tsx                # /gallery (作品广场)
└── admin/
    └── page.tsx                # /admin (管理后台)
```

---

## 设计系统

### 颜色主题
- 主色: 青色 → 紫色渐变 (`from-cyan-500 to-purple-500`)
- 强调色: `cyan-400`, `purple-500`, `amber-500`
- 背景: 深色 `#0a0a0f`
- 卡片背景: `white/5` ~ `white/10`

### UI库
- **图标**: `lucide-react`
- **动画**: `framer-motion`
- **Toast**: `sonner`
- **HTTP**: `axios`
- **状态**: `zustand`
- **数据获取**: `@tanstack/react-query`

---

## 待完成功能 (根据代码注释)

| 页面 | 功能 | 状态 |
|------|------|------|
| dashboard | 作品管理 | 开发中 |
| dashboard | 订单管理 | 开发中 |
| dashboard | 设置 | 部分完成 (API Key复制) |
| admin | 作品管理 | 占位 |
| admin | 订单管理 | 占位 |
| studio | 登录/注册 | UI占位 |
| studio | 个人中心 | UI占位 |
| gallery | 视频详情页 | 弹窗替代 |

---

## 总结

- **总页面数**: 8个
- **核心功能页面**: 1个 (studio)
- **用户相关页面**: 4个 (dashboard, pricing, templates, gallery)
- **工具页面**: 2个 (api-docs, admin)
- **入口页面**: 1个 (home)
- **完成度**: 约70% (部分功能为占位/开发中状态)
