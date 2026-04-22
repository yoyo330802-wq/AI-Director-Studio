# 漫AI 前端界面设计文档

> 版本: v1.0.0  
> 更新: 2026-04-14  
> 技术栈: Next.js 14 + Tailwind CSS + Framer Motion + Lucide Icons

---

## 📁 页面结构

```
frontend/app/
├── page.tsx              # 首页/落地页
├── layout.tsx           # 根布局
├── globals.css          # 全局样式
├── providers.tsx        # React Providers
│
├── studio/page.tsx      # 🎬 创作工作室 (核心页面)
├── pricing/page.tsx     # 💰 套餐定价
├── dashboard/page.tsx   # 👤 个人中心
├── gallery/page.tsx      # 🖼️ 作品广场
├── templates/page.tsx    # 📝 提示词模板
├── admin/page.tsx       # ⚙️ 管理后台
└── api-docs/page.tsx    # 📚 API文档
```

---

## 🎨 设计系统

### 色彩系统

| 名称 | 色值 | 用途 |
|------|------|------|
| Primary | `#8B5CF6` (紫色) | 主按钮、强调元素 |
| Secondary | `#EC4899` (粉色) | 渐变结束色 |
| Accent-Cyan | `#06B6D4` (青色) | 科技感强调 |
| Accent-Gradient | `purple → pink` | 品牌渐变 |
| Background-Dark | `#0a0a0f` | 深色模式背景 |
| Background-Light | `#f9fafb` | 浅色模式背景 |
| Success | `#10B981` | 成功状态 |
| Warning | `#F59E0B` | 警告状态 |
| Error | `#EF4444` | 错误状态 |

### 字体

- **主字体**: Inter (Google Fonts)
- **中文**: "PingFang SC", "Microsoft YaHei"
- **代码**: JetBrains Mono

### 圆角系统

| 尺寸 | 值 | 用途 |
|------|-----|------|
| sm | 8px | 小按钮、标签 |
| md | 12px | 输入框、小卡片 |
| lg | 16px | 卡片、面板 |
| xl | 24px | 大卡片、模态框 |
| 2xl | 32px | 主要容器 |

---

## 📄 页面详细设计

### 1. 首页 (page.tsx)

**路径**: `/`

**设计风格**: 浅色渐变背景，科技感落地页

**布局**:
```
┌─────────────────────────────────────────┐
│ Header: Logo + 导航 + 登录/注册按钮       │
├─────────────────────────────────────────┤
│ Hero Section:                           │
│   - 大标题 + 副标题                      │
│   - 主CTA按钮 (开始创作)                 │
│   - 动态背景渐变                        │
├─────────────────────────────────────────┤
│ Features: 3列特性介绍                   │
│   - 比官网便宜30%                        │
│   - 多种AI模型选择                       │
│   - 简单易用                            │
├─────────────────────────────────────────┤
│ Demo: 效果展示视频/图片                  │
├─────────────────────────────────────────┤
│ Pricing Preview: 价格预览                │
├─────────────────────────────────────────┤
│ Footer: 版权信息 + 链接                  │
└─────────────────────────────────────────┘
```

---

### 2. 创作工作室 (studio/page.tsx) ⭐ 核心

**路径**: `/studio`

**设计风格**: 浅灰背景，卡片式布局，深色顶部导航

**布局**:
```
┌────────────────────────────────────────────────────────────┐
│ Header (白色, sticky):                                     │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🎬 漫AI创作工作室  │  余额: ¥100.00  │  个人中心  │   │ │
│ └────────────────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────────────┤
│ 模式选择 (3列卡片):                                        │
│ ┌────────────┐ ┌────────────┐ ┌────────────┐            │
│ │ ⚡闪电模式  │ │ ✨智能模式  │ │ 👑专业模式  │            │
│ │ Wan2.1-1.3B│ │ 智能路由   │ │ Vidu/可灵  │            │
│ │ ¥0.04/秒  │ │ ¥0.06/秒  │ │ ¥0.09/秒  │            │
│ └────────────┘ └────────────┘ └────────────┘            │
├───────────────────────────────────┬────────────────────────┤
│ 左侧: 创作表单 (col-span-2)       │ 右侧: 状态/历史        │
│ ┌───────────────────────────────┐ │ ┌────────────────────┐│
│ │ ✍️ 提示词输入                 │ │ │ 当前任务状态        ││
│ │ [textarea]                   │ │ │ - 任务ID           ││
│ │                               │ │ │ - 状态: 排队中     ││
│ │ 🚫 负向提示词 (可选)          │ │ │ - 进度条           ││
│ │ [input]                      │ │ │ - 预计时间         ││
│ │                               │ │ └────────────────────┘│
│ │ ⏱️ 时长: [5秒] [10秒]        │ │                        │
│ │ 📐 比例: [横屏][竖屏][方形]   │ │ ┌────────────────────┐│
│ │                               │ │ │ 💡 灵感模板        ││
│ │ 🖼️ 参考图片上传               │ │ │ - 古风国漫         ││
│ │ [拖拽上传区]                  │ │ │ - 赛博朋克         ││
│ │                               │ │ │ - 日常治愈         ││
│ │ [▶ 立即生成 ¥0.30]           │ │ └────────────────────┘│
│ │ (渐变按钮)                   │ │                        │
│ └───────────────────────────────┘ │                        │
└───────────────────────────────────┴────────────────────────┘
```

**交互细节**:
- 模式切换: 卡片选中时有边框高亮 + 右上角对勾动画
- 提示词: 500字符限制，实时字数统计
- 生成按钮: 加载时显示旋转动画 + "生成中..."
- 进度更新: 模拟2秒间隔更新进度条

**组件**:
```typescript
// 模式配置
const MODES = {
  fast: {
    label: '闪电模式',
    icon: Zap,
    model: 'Wan2.1-1.3B',
    price: 0.04,
    color: 'from-yellow-400 to-orange-500',
  },
  balanced: {
    label: '智能模式',
    icon: Sparkles,
    model: '智能路由',
    price: 0.06,
    color: 'from-blue-400 to-purple-500',
  },
  premium: {
    label: '专业模式',
    icon: Crown,
    model: 'Vidu/可灵',
    price: 0.09,
    color: 'from-purple-500 to-pink-500',
  },
}
```

---

### 3. 套餐定价 (pricing/page.tsx)

**路径**: `/pricing`

**设计风格**: 深色背景，霓虹渐变标题，卡片式套餐

**布局**:
```
┌────────────────────────────────────────────────────────────┐
│ Header (深色渐变背景 + 模糊光效):                          │
│   选择您的创作方案                                         │
│   [月付] [年付 省20%]                                      │
├────────────────────────────────────────────────────────────┤
│ 套餐卡片 (4列网格):                                       │
│ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐             │
│ │ 体验版  │ │ 创作者 ★│ │ 工作室  │ │ 企业版  │             │
│ │ 免费    │ │ ¥39/月 │ │ ¥199/月│ │ ¥9999/年│            │
│ │ 5分钟   │ │ 60分钟  │ │ 300分钟 │ │ ∞分钟   │            │
│ │ ...    │ │ ...    │ │ ...    │ │ ...    │             │
│ │[免费]  │ │[购买]  │ │[购买]  │ │[购买]  │             │
│ └────────┘ └────────┘ └────────┘ └────────┘             │
├────────────────────────────────────────────────────────────┤
│ FAQ (2列):                                                │
│ ┌─────────────────────┐ ┌─────────────────────┐          │
│ │ 额度用完怎么办？     │ │ 可以退款吗？         │          │
│ └─────────────────────┘ └─────────────────────┘          │
│ ┌─────────────────────┐ ┌─────────────────────┐          │
│ │ 如何获取API权限？    │ │ 支持哪些支付方式？   │          │
│ └─────────────────────┘ └─────────────────────┘          │
└────────────────────────────────────────────────────────────┘
```

**套餐配置**:
| 套餐 | 价格 | 时长 | 额度 | 特性 |
|------|------|------|------|------|
| 体验版 | 免费 | - | 5分钟 | 基础模式, 720p |
| 创作者 | ¥39 | 30天 | 60分钟 | 全模式, 1080p, 无水印, API |
| 工作室 | ¥199 | 30天 | 300分钟 | 极速队列, 批量生成, 专属客服 |
| 企业版 | ¥9999 | 365天 | ∞分钟 | 专属GPU, 4K, SLA保障 |

**动画效果**:
- 页面入场: 卡片依次淡入上移 (delay: index * 0.1s)
- 推荐套餐: 渐变边框 + 阴影光效
- 年付切换: 平滑过渡动画

---

### 4. 个人中心 (dashboard/page.tsx)

**路径**: `/dashboard`

**设计风格**: 深色背景，侧边栏 + 主内容区布局

**布局**:
```
┌────────────────────────────────────────────────────────────┐
│ 侧边栏 (w-56):            │ 主内容区:                      │
│ ┌──────────────────────┐  │ ┌────────────────────────────┐│
│ │ [头像] 用户名         │  │ │ 统计卡片 (4列):            ││
│ │ 等级标签    VIP标识   │  │ │ ┌──┐ ┌──┐ ┌──┐ ┌──┐    ││
│ └──────────────────────┘  │ │ │余额│ │额度│ │已用│ │消费│││
│                            │ │ └──┘ └──┘ └──┘ └──┘    ││
│ [📊 概览]                  │ └────────────────────────────┘│
│ [🎬 我的作品]              │                                │
│ [💳 订单记录]              │ ┌────────────────────────────┐│
│ [💰 钱包]                  │ │ 最近任务                    ││
│ [👑 会员]                  │ │ [任务卡片列表]              ││
│ [⚙️ 设置]                  │ └────────────────────────────┘│
│                            │                                │
│ ┌──────────────────────┐  │ ┌────────────────────────────┐│
│ │ 快速操作:            │  │ │ VIP推广 (非VIP显示)         ││
│ │ [⚡ 开始创作]        │  │ └────────────────────────────┘│
│ └──────────────────────┘  │                                │
└────────────────────────────────────────────────────────────┘
```

**子页面**:

#### 4.1 概览 (OverviewSection)
- 4个统计卡片: 余额、额度、已用、累计消费
- 最近任务列表
- VIP升级推广

#### 4.2 我的作品 (VideosSection)
- 作品网格展示
- 状态: 生成中/已完成/失败

#### 4.3 订单记录 (OrdersSection)
- 订单列表: 订单号、金额、时间、状态
- 状态标签: 已支付(绿色)/待支付(灰色)

#### 4.4 钱包 (WalletSection)
- 渐变余额卡片
- 额度使用进度条

#### 4.5 会员 (SubscriptionSection)
- VIP状态展示卡
- 有效期信息
- VIP特权图标

#### 4.6 设置 (SettingsSection)
- 用户名编辑
- API Key复制
- 通知设置

---

### 5. 作品广场 (gallery/page.tsx)

**路径**: `/gallery`

**布局**:
```
┌─────────────────────────────────────────┐
│ 标签筛选: [全部] [古风] [赛博] [日常] ... │
├─────────────────────────────────────────┤
│ 瀑布流/网格布局:                         │
│ ┌─────┐ ┌─────────┐ ┌─────┐            │
│ │     │ │         │ │     │            │
│ │ 作品 │ │  作品   │ │ 作品 │            │
│ │     │ │         │ │     │            │
│ └─────┘ └─────────┘ └─────┘            │
│ ┌─────────┐ ┌─────┐ ┌─────────┐        │
│ │         │ │     │ │         │        │
│ │  作品   │ │ 作品 │ │  作品   │        │
│ │         │ │     │ │         │        │
│ └─────────┘ └─────┘ └─────────┘        │
└─────────────────────────────────────────┘
```

---

### 6. 提示词模板 (templates/page.tsx)

**路径**: `/templates`

**布局**:
```
┌─────────────────────────────────────────┐
│ 分类: [古风国漫] [赛博朋克] [日常治愈] ...│
├─────────────────────────────────────────┤
│ 模板卡片列表:                           │
│ ┌─────────────────────────────────────┐│
│ │ 模板名称                             ││
│ │ 预览提示词内容...                    ││
│ │ [使用] [复制]                       ││
│ └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

---

### 7. 管理后台 (admin/page.tsx)

**路径**: `/admin`

**功能** (预留):
- 用户管理
- 任务监控
- 渠道配置
- 数据统计

---

## 🧩 组件库

### 按钮组件

```typescript
// 主按钮 - 渐变背景
<button className="bg-gradient-to-r from-purple-500 to-pink-500 text-white">
  按钮文字
</button>

// 次按钮 - 透明背景
<button className="bg-white/10 hover:bg-white/20 text-white">
  按钮文字
</button>

// 禁用状态
<button className="opacity-50 cursor-not-allowed" disabled>
  按钮文字
</button>
```

### 卡片组件

```typescript
// 基础卡片
<div className="bg-white rounded-2xl shadow-lg p-6">
  {children}
</div>

// 深色卡片
<div className="bg-white/5 rounded-2xl p-6">
  {children}
</div>

// 选中卡片 (带边框高亮)
<div className="border-2 border-purple-500 shadow-lg">
  {children}
</div>
```

### 输入组件

```typescript
// 文本域
<textarea
  className="w-full h-32 p-4 border-2 border-gray-200 rounded-xl
             focus:border-purple-500 focus:ring-2 focus:ring-purple-200"
  placeholder="输入提示词..."
/>

// 输入框
<input
  type="text"
  className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl
             focus:border-purple-500 focus:ring-2 focus:ring-purple-200"
  placeholder="输入内容..."
/>
```

### 状态标签

```typescript
// 成功
<span className="px-3 py-1 rounded-full text-sm bg-green-100 text-green-700">
  已完成
</span>

// 处理中
<span className="px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-700">
  生成中
</span>

// 失败
<span className="px-3 py-1 rounded-full text-sm bg-red-100 text-red-700">
  失败
</span>

// 排队
<span className="px-3 py-1 rounded-full text-sm bg-yellow-100 text-yellow-700">
  排队中
</span>
```

---

## 📱 响应式断点

| 断点 | 宽度 | 用途 |
|------|------|------|
| sm | 640px | 手机横屏 |
| md | 768px | 平板 |
| lg | 1024px | 小笔记本 |
| xl | 1280px | 桌面 |
| 2xl | 1536px | 大屏 |

**响应式示例**:
```typescript
// 3列 → 2列 → 1列
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

// 隐藏移动端
<div className="hidden md:block">

// 仅移动端显示
<div className="md:hidden">
```

---

## 🎬 动画系统

使用 **Framer Motion** 实现动画:

```typescript
import { motion } from 'framer-motion'

// 入场动画 - 淡入上移
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
>
  {children}
</motion.div>

// 点击缩放
<motion.button
  whileHover={{ scale: 1.02 }}
  whileTap={{ scale: 0.98 }}
>
  按钮
</motion.button>

// 旋转动画 (加载中)
<motion.div
  animate={{ rotate: 360 }}
  transition={{ duration: 1, repeat: Infinity }}
/>
```

---

## 🔌 API 对接

### 前端 API 封装

```typescript
// lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

class ApiClient {
  private token: string | null = null

  setToken(token: string) {
    this.token = token
  }

  async request(method: string, path: string, data?: any) {
    const headers: any = { 'Content-Type': 'application/json' }
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`
    }

    const res = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: data ? JSON.stringify(data) : undefined,
    })

    if (!res.ok) throw new Error(await res.text())
    return res.json()
  }

  // 快捷方法
  get(path: string) { return this.request('GET', path) }
  post(path: string, data: any) { return this.request('POST', path, data) }
}

export default new ApiClient()
```

### API 端点映射

| 前端调用 | 后端端点 | 方法 |
|---------|---------|------|
| `api.getCurrentUser()` | `/v1/users/me` | GET |
| `api.previewRoute(mode, duration)` | `/v1/generate/route/preview` | GET |
| `api.createTask(params)` | `/v1/generate` | POST |
| `api.getBalance()` | `/v1/bill/balance` | GET |
| `api.recharge(amount)` | `/v1/bill/recharge` | POST |
| `api.getPackages()` | `/v1/bill/packages` | GET |

---

## 📦 第三方库

| 库 | 版本 | 用途 |
|----|------|------|
| next | 14.x | React框架 |
| react | 18.x | UI库 |
| tailwindcss | 3.x | 样式框架 |
| framer-motion | 11.x | 动画 |
| lucide-react | latest | 图标 |
| @tanstack/react-query | 5.x | 数据请求 |
| sonner | 1.x | Toast通知 |
| zustand | 4.x | 状态管理 |

---

## 🔧 开发指南

### 启动开发服务器
```bash
cd frontend
npm run dev
# 访问 http://localhost:3000
```

### 构建生产版本
```bash
npm run build
npm run start
```

### 添加新页面
1. 在 `app/` 下创建 `[page]/page.tsx`
2. 使用布局组件包装
3. 添加导航链接

---

*文档生成时间: 2026-04-14*
