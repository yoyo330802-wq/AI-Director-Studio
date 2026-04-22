# SPEC: 漫AI / ComfyUI Orchestrator — Sprint 1

> PRD: PRD_v2.1.md
> 项目定位: 专业动漫团队AI生产力工具 = ComfyUI工作流编排 + 漫AI品牌(用户+计费+路由)
> Sprint: S1 — 后端核心API + ComfyUI集成

---

## Vision

专业动漫团队使用的AI视频生成平台。底层基于ComfyUI执行Wan2.1工作流（自建H100集群），外层叠加漫AI品牌：智能路由、Token计费、用户管理。通过免费算力获客，用高质量作品和专业知识变现。

---

## What We're Building in Sprint 1

### 架构总览

```
用户请求
    ↓
漫AI Backend (FastAPI)
    ├── 用户系统 (F001)
    ├── 计费系统 (F002)
    ├── 智能路由 (F003) ← 选择执行策略
    └── 任务队列 (Celery)
            ↓
    ┌───────┴───────┐
    ↓               ↓
ComfyUI          外部API
(自建H100)       (硅基流动-Vidu/KLing)
    ↓
执行工作流
```

### F001: 用户系统

**Endpoints:**
```
POST /api/v1/auth/register
  Request:  {email, password, name}
  Response: 201 {user_id, email, token_balance}

POST /api/v1/auth/login
  Request:  {email, password}
  Response: 200 {access_token, token_type}

GET /api/v1/users/me
  Headers: Authorization: Bearer <token>
  Response: 200 {user_id, email, name, token_balance}
```

### F002: 计费系统

**规则:**
- 新用户初始 Token: 100
- 扣费 = duration(秒) × 单价
- 提交任务前检查余额
- 余额不足返回 402

**单价表:**

| 模式 | 单价 | 说明 |
|------|------|------|
| cost | ¥0.04/秒 | Wan2.1-1.3B, ~15秒出片 |
| balanced | ¥0.06/秒 | 智能路由 |
| quality | ¥0.09/秒 | Vidu/可灵 |

### F003: 智能路由引擎

**策略:**
- `cost`: Wan2.1-1.3B via ComfyUI (H100集群)
- `quality`: Vidu via 硅基流动API
- `balanced`: 70% Wan2.1 + 30% Vidu (按生成时长比例)

**执行路径:**
```
cost模式 → ComfyUI → Wan2.1 Custom Node → H100集群
quality模式 → 硅基流动API → Vidu
balanced模式 → 自动选择
```

**降级规则:**
- ComfyUI不可用 → 降级到硅基流动
- 硅基流动不可用 → 降级到其他API

### F004: 任务系统

**Endpoints:**
```
POST /api/v1/generate
  Request:  {prompt, duration, quality_mode, aspect_ratio}
  Response: 202 {task_id, status, estimated_time}

GET /api/v1/generate/{task_id}
  Response: 200 {task_id, status, progress, video_url, error}

WebSocket /ws/tasks/{task_id}
  推送: {progress, status, video_url}
```

**状态流转:** queued → processing → completed/failed

---

## Data Models

### User (新增)
```python
class User(SQLModel, table=True):
    id: int = Field(primary_key=True)
    email: str = Field(unique=True, index=True)
    name: str
    hashed_password: str
    token_balance: int = Field(default=100)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### GenerationTask (新增)
```python
class GenerationTask(SQLModel, table=True):
    id: str = Field(primary_key=True, default_factory=lambda: str(uuid4()))
    user_id: int = Field(foreign_key="user.id")
    prompt: str
    duration: int
    quality_mode: str
    aspect_ratio: str
    status: str = Field(default="queued")
    progress: int = Field(default=0)
    video_url: Optional[str] = None
    error: Optional[str] = None
    token_cost: float
    execution_path: str  # "comfyui_wan21" | "siliconflow_vidu" | "siliconflow_kling"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
```

### Workflow (已有)
- 复用 ComfyUI Orchestrator 的 Workflow 模型
- 存储预定义工作流配置

### NodeType (已有)
- 复用 ComfyUI Orchestrator 的 NodeType 模型
- 从 ComfyUI /object_info 同步

---

## Technical Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14 |
| Backend | FastAPI + SQLModel + Pydantic v2 |
| Execution | ComfyUI (H100集群) + 硅基流动API |
| Database | PostgreSQL 16 |
| Cache/Queue | Redis + Celery |
| Storage | MinIO |
| Auth | JWT (python-jose + passlib) |

---

## ComfyUI 集成

### ComfyUI 连接
```python
COMFYUI_URL: str = "http://localhost:8188"  # H100集群地址

# 调用ComfyUI执行工作流
POST {COMFYUI_URL}/api/prompt
{
    "prompt": {
        "node_id": {
            "class_type": "Wan21Video",
            "inputs": {"prompt": "...", "duration": 5}
        }
    }
}
```

### 硅基流动 API (外部模型)
```python
# Vidu / 可灵 via 硅基流动
SILICONFLOW_API_KEY: str
SILICONFLOW_API_URL: str = "https://api.siliconflow.cn/v1"

# 统一调用接口
async def generate_video(prompt, duration, model):
    # model: "vidu" | "kling"
```

---

## API Error Format

All errors: `{"detail": str}`

| Status | Meaning |
|--------|---------|
| 400 | Bad Request |
| 401 | Unauthorized |
| 402 | Payment Required (余额不足) |
| 404 | Not Found |
| 409 | Conflict |
| 422 | Validation Error |
| 500 | Internal Error |

---

## Evaluation Criteria

### Feature Completeness (25%)
- [ ] F001: 用户注册/登录/查询
- [ ] F002: Token余额/扣费
- [ ] F003: 3种路由模式
- [ ] F004: 任务提交/进度/WebSocket

### Functionality (20%)
- [ ] JWT认证正确
- [ ] 余额检查正确
- [ ] 任务状态正确
- [ ] WebSocket推送

### Code Quality (20%)
- [ ] 类型提示完整
- [ ] response_model覆盖
- [ ] 错误处理显式

### AI Integration (10%)
- [ ] ComfyUI客户端(模拟)
- [ ] 硅基流动客户端(模拟)
- [ ] 路由逻辑正确

### Security (5%)
- [ ] 密码bcrypt hash
- [ ] JWT有效期
- [ ] 输入验证

### Performance (5%)
- [ ] 提交<200ms
- [ ] 无N+1查询

### Visual Design (15%) - S2启用

---

## Pass Threshold: 7.0

## Critical Issues (auto-FAIL)
1. JWT secret hardcoded
2. Password plain text
3. No balance check
4. Celery task not idempotent
5. SQL injection
