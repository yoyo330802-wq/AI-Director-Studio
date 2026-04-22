# SPEC.md — Sprint 7: Hermes Multi-Agent REST API 集成

**基于**：`hermes.py` + `core/lock.py` + `backend/app/hermes/`  
**创建日期**：2026-04-18  
**Phase**：Phase 0-2（PRD质疑 + 规格制定 + Sprint Contract）

---

## 一、Feature 定义

### 1.1 核心功能
将 Hermes 多 Agent 编排系统以 REST API + WebSocket 方式接入漫AI后端，使外部（前端/飞书/其他客户端）可通过 API 调用 Hermes 的 GAN 工作流执行引擎。

### 1.2 解决的问题
- 此前 Hermes 只在 Docker 内运行，无法从 HTTP 调用
- 现在可以通过 `POST /api/v1/hermes/tasks` 触发 GAN 工作流
- WebSocket 实时推送 Phase 进度

---

## 二、API 规格

### 2.1 REST Endpoints

```
POST   /api/v1/hermes/tasks              # 提交任务 → {task_id}
GET    /api/v1/hermes/tasks              # 列出任务（分页）
GET    /api/v1/hermes/tasks/{task_id}    # 获取任务详情
DELETE /api/v1/hermes/tasks/{task_id}    # 取消任务
GET    /api/v1/hermes/agents             # 列出可用 Agent 类型
GET    /api/v1/hermes/stats              # 全局统计
GET    /api/v1/hermes/evolution/suggestions?agent_type=xxx  # 优化建议
```

### 2.2 WebSocket
```
WS /api/v1/hermes/events/{task_id}?token={jwt}
```
实时推送：`connected | heartbeat | TASK_PROGRESS | AGENT_MESSAGE | TASK_COMPLETED | TASK_FAILED`

### 2.3 请求/响应示例

**POST /api/v1/hermes/tasks**
```json
// Request
{
  "command": "开发用户登录功能",
  "sprint": 1
}

// Response
{
  "task_id": "hms_abc123",
  "command": "开发用户登录功能",
  "agent_type": "engineer",
  "status": "NEW",
  "current_phase": 0,
  "overall_progress": 0,
  "created_at": "2026-04-18T..."
}
```

**WebSocket 推送示例**
```json
{"event": "PHASE_STARTED", "task_id": "hms_abc123", "phase": 0, "progress": 10}
{"event": "TASK_PROGRESS", "task_id": "hms_abc123", "phase": 1, "progress": 25, "data": {"message": "SPEC 生成中"}}
{"event": "AGENT_MESSAGE", "task_id": "hms_abc123", "data": {"output": "Phase 2: Sprint Contract 已生成"}}
{"event": "TASK_COMPLETED", "task_id": "hms_abc123", "progress": 100, "data": {"status": "completed"}}
```

---

## 三、数据模型

### HermesTask（PostgreSQL 持久化）
```python
id: str                    # "hms_" + uuid4 前8位
command: str               # 用户指令
agent_type: str            # "engineer" | "researcher" | "creator"
status: Enum               # NEW | QUEUED | IN_PROGRESS | COMPLETED | FAILED | CANCELLED
current_phase: int         # 0-8
overall_progress: int      # 0-100
sprint: int | None         # GAN Sprint 编号
scores: JSON | None        # {"Sprint 1": 8.5, ...}
result: JSON | None        # 最终结果
error_message: str | None
created_at: datetime
updated_at: datetime
completed_at: datetime | None
```

### HermesEvent（Redis pub/sub，临时）
```python
event: Enum                # TASK_ASSIGNED | PHASE_STARTED | TASK_PROGRESS | AGENT_MESSAGE | TASK_COMPLETED | TASK_FAILED
task_id: str
phase: int | None
progress: int | None
data: dict
timestamp: datetime
```

---

## 四、路由逻辑

```
用户指令含 "开发/代码/系统/网站"  → agent_type = "engineer"（走 GAN Phase 0-8）
用户指令含 "调研/分析/竞品"      → agent_type = "researcher"（直接执行）
用户指令含 "方案/文案/脚本"      → agent_type = "creator"（直接执行）
```

---

## 五、依赖关系

```
hermes.py          ← API 入口，依赖以下模块
  ├── hermmes/models.py    ← HermesTask, HermesEvent 数据模型
  ├── hermes/state.py      ← 状态管理（Redis实时 + PostgreSQL持久）
  ├── hermes/router.py     ← 指令路由到 Agent 类型
  ├── hermes/gan_runner.py ← GAN 工作流执行器
  ├── hermes/executor.py   ← Docker Agent 执行器
  ├── hermes/evolution.py  ← 进化引擎（日志/决策库/优化建议）
  └── core/lock.py          ← 分布式锁（支付幂等，也供其他服务使用）
```

---

## 六、关键设计决策

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 任务状态存储 | PostgreSQL（持久）+ Redis（实时） | 兼顾可靠性 + 低延迟事件推送 |
| Agent 执行方式 | Docker 容器（`hermes-company/`） | 隔离环境，支持 Claude Code / Codex 等 |
| Engineering 任务 | 走完整 GAN Phase 0-8 | 与漫AI开发规范一致 |
| 事件推送 | Redis pub/sub → WebSocket | 支持多客户端订阅同一任务 |
| 认证 | JWT Bearer Token | 复用现有 `get_current_user` |

---

## 七、文件清单

```
backend/app/
├── api/
│   └── hermes.py              ← REST + WebSocket API（已存在）
├── core/
│   └── lock.py                ← 分布式锁（已存在）
├── hermes/
│   ├── __init__.py
│   ├── models.py              ← HermesTask, HermesEvent 模型
│   ├── state.py               ← 状态管理
│   ├── router.py              ← 任务路由
│   ├── gan_runner.py          ← GAN Runner
│   ├── executor.py            ← Docker Agent 执行器
│   └── evolution.py           ← 进化引擎
hermes-company/
├── Dockerfile                  ← Agent 镜像
├── config/agents.yaml          ← Agent 配置
└── shared/                    ← 共享文件
```

---

## 八、已实现状态

| 模块 | 状态 | 文件 |
|------|------|------|
| REST API | ✅ 已完成 | `hermes.py` |
| WebSocket | ✅ 已完成 | `hermes.py` |
| Distributed Lock | ✅ 已完成 | `core/lock.py` |
| Hermes Models | ✅ 已完成 | `hermes/models.py` |
| Hermes State | ✅ 已完成 | `hermes/state.py` |
| Task Router | ✅ 已完成 | `hermes/router.py` |
| GAN Runner | ✅ 已完成 | `hermes/gan_runner.py` |
| Executor | ✅ 已完成 | `hermes/executor.py` |
| Evolution Engine | ✅ 已完成 | `hermes/evolution.py` |
| Docker Agent Image | ⚠️ 待构建 | `hermes-company/Dockerfile` |

---

## 九、待完成项（Phase 3 评分后）

- Docker Image 构建并测试
- API 端到端测试（提交任务 → WebSocket 收进度 → 完成）
- JWT 认证集成验证
- `main.py` 注册 `hermes_router` 确认
