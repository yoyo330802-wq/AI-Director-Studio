# 漫AI 后端模块盘点报告

**盘点时间**: 2026-04-15
**项目路径**: `/home/wj/workspace/manai/backend`
**技术栈**: FastAPI + SQLModel + Pydantic v2 + Celery + Redis

---

## 一、API 模块 (app/api/)

### 1. auth.py - 认证API `/api/v1/auth`
| 端点 | 方法 | 功能 |
|------|------|------|
| `/register` | POST | 用户注册 |
| `/login` | POST | 用户登录，返回JWT Token |

**核心依赖**: `User` model, `security` (hash_password, verify_password, create_access_token)

---

### 2. users.py - 用户API `/api/v1/users`
| 端点 | 方法 | 功能 |
|------|------|------|
| `/me` | GET | 获取当前用户信息 |

**核心依赖**: `User` model, `get_current_user`

---

### 3. generate.py - 视频生成API `/api/v1/generate`
| 端点 | 方法 | 功能 |
|------|------|------|
| `/` | POST | 提交视频生成任务 (202 Accepted) |
| `/route/preview` | GET | 路由预览，显示将使用的模型和预估信息 |
| `/{task_id}` | GET | 查询任务状态 |

**核心依赖**:
- `GenerationTask` model
- `services.billing` (calculate_cost_tokens, validate_balance, get_estimated_time, PRICING)
- `services.router` (get_execution_path)
- `tasks.video_generation` (submit_generation_task)

---

### 4. generation.py - 视频生成API (旧版/冗余) `/api/v1`
| 端点 | 方法 | 功能 |
|------|------|------|
| `/` | POST | 创建视频生成任务 |
| `/tasks` | GET | 获取任务列表 (分页) |
| `/tasks/{task_id}` | GET | 获取任务状态 |
| `/tasks/{task_id}` | DELETE | 取消任务 |
| `/tasks/{task_id}/callback` | POST | 第三方回调接口 |

**核心依赖**: `generation_service`, `Task` model

**注意**: 此文件与 `generate.py` 功能重叠，属于新旧版本并存

---

### 5. billing.py - 计费API `/api/v1/billing`
| 端点 | 方法 | 功能 |
|------|------|------|
| `/balance` | GET | 获取余额信息 |
| `/recharge` | POST | 充值 (直接到账) |
| `/transactions` | GET | 获取交易记录 |
| `/packages` | GET | 获取套餐列表 |

**核心依赖**: `User`, `Order`, `PaymentTransaction` models

---

### 6. payment.py - 支付API `/api/v1/payment`
| 端点 | 方法 | 功能 |
|------|------|------|
| `/create` | POST | 创建充值订单 |
| `/notify/alipay` | POST | 支付宝异步回调 |
| `/notify/wechat` | POST | 微信支付异步回调 |
| `/status/{order_no}` | GET | 查询订单状态 |
| `/list` | GET | 获取订单列表 |
| `/packages` | GET | 获取套餐列表 |
| `/packages/{package_id}` | GET | 获取套餐详情 |

**核心类**:
- `AlipayService` - 支付宝支付服务 (RSA2签名)
- `WechatPayService` - 微信支付服务 (MD5签名)

**注意**: 此文件与 `billing.py` 功能重叠，支付流程实现不完整

---

### 7. websocket.py - WebSocket API
| 端点 | 方法 | 功能 |
|------|------|------|
| `/ws/tasks/{task_id}` | WS | WebSocket推送任务进度 (Redis pub/sub) |

**核心类**: `ConnectionManager` - Redis pub/sub版本的连接管理器

---

## 二、服务模块 (app/services/)

### 1. billing.py - 计费服务
**定价表** (元/秒):
| 模式 | 单价 |
|------|------|
| cost | 0.04 |
| balanced | 0.06 |
| quality | 0.09 |

**预估生成时间** (秒):
| 模式 | 时间 |
|------|------|
| cost | 15 |
| balanced | 30 |
| quality | 60 |

**函数**:
- `calculate_cost(duration, quality_mode)` - 计算生成费用
- `calculate_cost_tokens(duration, quality_mode)` - 计算Token消耗 (1 Token = 0.01元)
- `get_estimated_time(quality_mode)` - 获取预估生成时间
- `validate_balance(balance, duration, quality_mode)` - 验证余额是否足够

---

### 2. generation.py - 视频生成服务
**核心类**: `GenerationService`

**支持的提供商**:
- `VideoProvider.WAN_1_3B` - Wan2.1-1.3B
- `VideoProvider.WAN_14B` - Wan2.1-14B
- `VideoProvider.VIDU` - Vidu
- `VideoProvider.KLING` - 可灵

**主要方法**:
- `create_task(db, user_id, request)` - 创建生成任务
- `get_task_status(db, task_id, user_id)` - 获取任务状态
- `_process_task(task_id)` - 处理任务 (异步)
- `_call_provider(provider, task, request)` - 调用提供商API
- `_mock_generate(task)` - 模拟生成 (开发环境)

**Provider配置**:
```python
{
    "endpoint": settings.XXX_ENDPOINT,
    "api_key": settings.XXX_API_KEY,
    "timeout": 120-300,
    "max_retries": 1-2,
}
```

---

### 3. router.py - 智能路由服务
**路由策略**:
- `QualityMode.COST` → `ExecutionPath.COMFYUI_WAN21` (Wan2.1-1.3B)
- `QualityMode.QUALITY` → `ExecutionPath.SILICONFLOW_VIDU` (Vidu)
- `QualityMode.BALANCED` → 30秒内用Wan2.1，超过用Vidu

**函数**:
- `get_execution_path(quality_mode, duration)` - 确定执行路径
- `is_comfyui_path(execution_path)` - 判断是否为ComfyUI路径
- `is_siliconflow_path(execution_path)` - 判断是否为硅基流动路径

---

### 4. router/smart_router.py - 智能路由引擎
**核心类**: `SmartRouter`

**可用渠道配置**:
| 渠道ID | 名称 | 成本(元/秒) | 质量评分 | 平均生成时间 | 最大队列 | 支持功能 |
|--------|------|-------------|----------|--------------|----------|----------|
| wan21_1.3b | Wan2.1-1.3B(自建) | 0.012 | 6 | 15秒 | 100 | text2video |
| wan21_14b | Wan2.1-14B(自建) | 0.025 | 7 | 30秒 | 50 | text2video, image2video |
| vidu | Vidu(硅基流动) | 0.050 | 8 | 45秒 | 30 | text2video, image2video, anime_style |
| kling | 可灵(硅基流动) | 0.070 | 9 | 60秒 | 20 | text2video, image2video, motion_brush, camera_control |

**路由决策算法**:
1. 强制指定 (企业用户)
2. 质量优先 → 可灵
3. 成本优先 → Wan2.1-1.3B
4. 特殊功能需求 → Vidu/可灵
5. 智能平衡模式 (默认)

**智能平衡评分公式**:
```
Score = w1*cost + w2*quality + w3*load + w4*speed
```

**用户等级权重**:
| 等级 | cost | quality | load | speed |
|------|------|---------|------|-------|
| free | 0.6 | 0.2 | 0.1 | 0.1 |
| basic | 0.4 | 0.3 | 0.2 | 0.1 |
| pro | 0.2 | 0.5 | 0.2 | 0.1 |
| enterprise | 0.1 | 0.3 | 0.2 | 0.4 |

---

## 三、客户端模块 (app/clients/)

### 1. comfyui_client.py - ComfyUI Wan2.1客户端
**核心类**: `ComfyUIClient`

**API端点**:
- `GET /system_stats` - 系统状态
- `POST /api/prompt` - 提交工作流
- `GET /history/{prompt_id}` - 获取执行结果
- `GET /queue` - 队列状态

**主要方法**:
- `get_system_stats()` - 获取系统状态
- `is_available()` - 检查服务是否可用
- `queue_prompt(prompt)` - 提交工作流到队列
- `get_history(prompt_id)` - 获取执行历史
- `get_queue()` - 获取队列状态
- `build_wan21_workflow(...)` - 构建Wan2.1 ComfyUI工作流
- `generate_video(...)` - 文本生视频 (提交+轮询)

---

### 2. siliconflow_client.py - 硅基流动API客户端
**核心类**: `SiliconFlowClient`

**API端点**: `https://api.siliconflow.cn/v1`

**主要方法**:
- `generate_video(model, prompt, duration, aspect_ratio)` - 提交视频生成任务
- `get_task_status(task_id)` - 查询任务状态
- `is_available()` - 检查API是否可用

**支持模型**: `vidu`, `kling`

---

### 3. vidu_client.py - Vidu API客户端
**核心类**: `ViduClient`

**API端点**: `https://api.vidu.cn/v1`

**主要方法**:
- `text_to_video(prompt, style, duration, resolution)` - 文生视频 (动漫风格优化)
- `image_to_video(image_url, prompt, duration)` - 图生视频
- `refer_to_video(reference_url, prompt, duration)` - 参考生视频 (多主体参考)
- `enhance(video_url)` - 智能超清 (1080P, 24帧)
- `health_check()` - 健康检查

**定价**: 0.050 元/秒

---

### 4. wan21_client.py - Wan2.1自建集群客户端
**核心类**: `Wan21Client`

**API端点**: `http://wan21.internal.manai.com/v1/generate/{model_size}`

**支持的模型**: `14b`, `1.3b`

**主要方法**:
- `text_to_video(prompt, negative_prompt, duration, resolution, aspect_ratio, seed)` - 文生视频
- `image_to_video(image_url, prompt, duration)` - 图生视频
- `_optimize_prompt(prompt)` - 针对Wan2.1优化提示词
- `_format_size(resolution, aspect_ratio)` - 格式化分辨率参数
- `health_check()` - 健康检查

**定价**:
| 模型 | 成本(元/秒) |
|------|-------------|
| 14b | 0.025 |
| 1.3b | 0.012 |

**注意**: 1.3B模型仅支持5秒视频，不支持图生视频

---

## 四、任务模块 (app/tasks/)

### video_generation.py - 视频生成Celery任务
**Celery配置**:
- Broker: Redis
- Task serializer: JSON
- Time limit: 600秒 (10分钟)

**主要函数**:
- `submit_generation_task(task_id)` - 提交生成任务到Celery
- `process_generation_task(task_id)` - 异步执行视频生成任务

**执行流程**:
1. 获取任务信息
2. 根据执行路径选择生成方式:
   - `is_comfyui_path` → `_generate_via_comfyui()`
   - `is_siliconflow_path` → `_generate_via_siliconflow()`
3. 更新任务状态和进度
4. 扣除用户Token

**辅助函数**:
- `_generate_via_comfyui(task)` - 通过ComfyUI Wan2.1生成
- `_generate_via_siliconflow(task)` - 通过硅基流动API生成
- `_update_task_progress(task_id, progress)` - 更新任务进度
- `_deduct_user_tokens(session, user_id, tokens)` - 扣除用户Token

---

## 五、数据模型 (app/models/)

### 1. database.py / db.py - 数据库模型
**核心表**:
- `User` - 用户表
- `Task` - 任务表
- `Order` - 订单表
- `Package` - 套餐表
- `PaymentTransaction` - 支付交易表
- `ChannelConfig` - 渠道配置表

### 2. user.py - 用户模型 (async)
**主要字段**: id, email, name, hashed_password, token_balance, is_active, created_at

### 3. task.py - 任务模型 (async)
**主要字段**: id, user_id, prompt, duration, quality_mode, aspect_ratio, status, progress, video_url, token_cost, execution_path

### 4. schemas.py - Pydantic模型
**用户相关**: UserRegister, UserLogin, UserUpdate, UserResponse, Token, BalanceResponse

**生成相关**: GenerationMode, GenerationRequest, GenerationResponse, TaskStatus, TaskListResponse

**支付相关**: RechargeRequest, RechargeResponse, OrderResponse, PackageResponse, TransactionResponse

**其他**: VideoResponse, TemplateResponse, PageResponse, MessageResponse, ErrorResponse

---

## 六、核心配置 (app/config.py)

**Settings类主要配置**:
```python
APP_NAME = "漫AI - 动漫创作Token平台"
VERSION = "0.1.0"

# 数据库
DATABASE_URL = "postgresql+asyncpg://manai:manai123@localhost:5432/manai"
REDIS_URL = "redis://localhost:6379/0"

# 安全
SECRET_KEY = "manai-secret-key-change-in-production-2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7天

# 上游API
SILICONFLOW_API_KEY, VIDU_API_KEY, VIDU_API_BASE
WAN21_BASE_URL, WAN21_API_KEY
COMFYUI_URL, COMFYUI_API_KEY
WAN21_COMFYUI_URL, WAN21_COMFYUI_API_KEY

# 计费
PRICING = {"fast": 0.04, "balanced": 0.06, "premium": 0.09}
COSTS = {"wan21_1.3b": 0.012, "wan21_14b": 0.025, "vidu": 0.050, "kling": 0.070}
```

---

## 七、入口文件 (app/main.py)

**已注册的路由**:
1. `auth_router` - 认证
2. `users_router` - 用户
3. `generate_router` - 视频生成
4. `websocket_router` - WebSocket

**健康检查端点**:
- `GET /api/v1/health` - 返回 `{"status": "ok", "version": "0.1.0"}`
- `GET /` - 返回应用信息

---

## 八、模块依赖关系图

```
main.py
├── auth.py (API)
│   └── services/billing.py
├── users.py (API)
├── generate.py (API)
│   ├── services/billing.py
│   ├── services/router.py
│   └── tasks/video_generation.py
│       ├── clients/comfyui_client.py
│       ├── clients/siliconflow_client.py
│       └── api/websocket.py
├── generation.py (API) [旧版/冗余]
│   └── services/generation.py
├── billing.py (API)
├── payment.py (API)
│   ├── models/database.py (Order, PaymentTransaction, Package)
│   └── core/security.py
└── websocket.py (API)
    └── tasks/video_generation.py

router/smart_router.py (智能路由引擎)
├── wan21_client.py
├── vidu_client.py
└── siliconflow_client.py
```

---

## 九、待完善/问题

1. **代码冗余**: `generation.py` 与 `generate.py` 功能重叠，`billing.py` 与 `payment.py` 部分功能重叠
2. **支付流程不完整**: `payment.py` 中支付宝/微信回调为空实现
3. **旧版模型并存**: 同时存在 `models/database.py` (sync) 和 `models/user.py` (async)、`models/task.py` (async)
4. **客户端降级逻辑**: `tasks/video_generation.py` 中 ComfyUI 不可用时降级到 SiliconFlow
5. **智能路由未完全集成**: `router/smart_router.py` 是完整实现但 `generation.py` 使用的是简化版 `services/router.py`

---

## 十、文件清单

```
backend/app/
├── __init__.py
├── main.py                 # FastAPI 入口
├── config.py                # 配置
├── database.py              # 异步数据库会话
├── api/
│   ├── __init__.py
│   ├── auth.py              # 认证 API
│   ├── users.py             # 用户 API
│   ├── generate.py          # 视频生成 API (新版)
│   ├── generation.py        # 视频生成 API (旧版)
│   ├── billing.py           # 计费 API
│   ├── payment.py           # 支付 API
│   └── websocket.py         # WebSocket API
├── clients/
│   ├── __init__.py
│   ├── comfyui_client.py    # ComfyUI Wan2.1 客户端
│   ├── siliconflow_client.py # 硅基流动客户端
│   ├── vidu_client.py       # Vidu 客户端
│   └── wan21_client.py      # Wan2.1 自建集群客户端
├── models/
│   ├── __init__.py
│   ├── database.py           # 数据库模型 (sync)
│   ├── db.py                # 数据库会话
│   ├── schemas.py            # Pydantic 模型
│   ├── user.py              # 用户模型 (async)
│   └── task.py              # 任务模型 (async)
├── router/
│   ├── __init__.py
│   └── smart_router.py      # 智能路由引擎
├── services/
│   ├── __init__.py
│   ├── billing.py           # 计费服务
│   ├── generation.py        # 生成服务
│   └── router.py            # 路由服务 (简化版)
├── tasks/
│   ├── __init__.py
│   └── video_generation.py  # Celery 视频生成任务
└── core/
    └── security.py          # 安全工具 (JWT, 密码哈希)
```
