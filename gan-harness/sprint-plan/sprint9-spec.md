# Sprint 9 SPEC — 飞书机器人集成 + E2E测试

**日期**: 2026-04-19
**Sprint**: S9
**优先级**: P0

---

## 1. 功能规格

### S9-F1: 飞书机器人 Webhook 集成

**目标**: 接入飞书机器人，实现消息接收和卡片消息推送

**飞书应用配置**:
- app_id: `cli_a92ee0821db8dcc4`
- app_secret: `q6nCESAMiE12vi8feEubth50FLPciC1I`

**实现内容**:
1. 新建 `backend/app/api/feishu_bot.py`
2. `POST /api/v1/feishu/webhook` - 接收飞书事件（支持 `im.message.receive_v1` 事件）
3. 飞书消息推送 - 卡片消息格式（Interactive Card）
4. 签名验证 - `X-Lark-Signature` header 验签

**飞书卡片消息格式**:
```json
{
  "msg_type": "interactive",
  "card": {
    "header": {
      "title": {"tag": "plain_text", "content": "任务进度"},
      "template": "blue"
    },
    "elements": [
      {"tag": "div", "content": {"tag": "lark_md", "content": "**任务ID**: task_123"}},
      {"tag": "hr"},
      {"tag": "div", "content": {"tag": "lark_md", "content": "**进度**: 50%"}}
    ]
  }
}
```

**验签逻辑**:
```
signature = HMAC-SHA256(app_secret, timestamp + "+" + body)
验证: timing_safe_compare(signature, X-Lark-Signature)
```

---

### S9-F2: 端到端 API 测试自动化

**目标**: 用 subprocess + curl 测试关键流程

**测试用例**:
1. **注册 → 登录 → 创建Hermes任务**
   - POST /api/v1/auth/register
   - POST /api/v1/auth/login
   - POST /api/v1/hermes/tasks
   
2. **WebSocket 连接 → 接收事件**
   - 建立 WebSocket 连接
   - 验证连接成功收到初始状态
   
3. **GET /api/v1/hermes/tasks 验证用户隔离**
   - 用户A创建的任务，用户B无法访问

**输出**: `backend/tests/hermes_e2e_test.py`

---

### S9-F3: 飞书机器人接入漫AI工作流

**目标**: 飞书发消息 → Hermes API 创建任务 → WebSocket 推送进度 → 飞书卡片消息回复

**流程**:
1. 飞书用户发送消息到机器人
2. 飞书服务器回调 `POST /api/v1/feishu/webhook`
3. 解析用户指令，创建 Hermes 任务
4. 任务进度通过 WebSocket 实时推送
5. 任务完成后，调用飞书 API 发送卡片消息

**飞书 API 调用**:
- 获取tenant_access_token: `POST https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal`
- 发送消息: `POST https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id`

---

### S9-F4: WebSocket JWT 优化

**目标**: 将 token 从 query param 改为 header 传递

**当前问题**:
```
ws://localhost:8000/api/v1/hermes/events/{task_id}?token={jwt}
```

**优化后**:
```
ws://localhost:8000/api/v1/hermes/events/{task_id}
Header: Authorization: Bearer <jwt>
```

**修改点**:
- `backend/app/api/hermes.py` 第342-347行
- 使用 `WebSocket.headers` 获取 `Authorization` header
- 同时兼容旧版 query param（向后兼容）

---

## 2. API 规格

### POST /api/v1/feishu/webhook
```
Headers:
  X-Lark-Signature: <签名>
  X-Lark-Request-Timestamp: <时间戳>
  Content-Type: application/json

Body:
{
  "schema": "2.0",
  "header": {
    "event_id": "xxx",
    "event_type": "im.message.receive_v1",
    "create_time": "2026-04-19T00:00:00Z"
  },
  "event": {
    "sender": {"sender_id": {"open_id": "ou_xxx"}},
    "message": {
      "message_id": "om_xxx",
      "content": "{\"text\":\"开发一个登录功能\"}"
    }
  }
}

Response: {"code": 0, "msg": "success"}
```

### GET /api/v1/hermes/tasks (新增 Header Auth)
```
Headers:
  Authorization: Bearer <jwt>

Response: {
  "items": [...],
  "total": 10,
  "page": 1,
  "limit": 20
}
```

---

## 3. 数据模型

### FeishuMessageRequest (新)
```python
class FeishuMessageRequest(BaseModel):
    schema: str
    header: FeishuEventHeader
    event: FeishuMessageEvent
```

### FeishuConfig (新增配置)
```python
# app/config.py
FEISHU_APP_ID: str = "cli_a92ee0821db8dcc4"
FEISHU_APP_SECRET: str = "q6nCESAMiE12vi8feEubth50FLPciC1I"
FEISHU_VERIFICATION_TOKEN: str = ""  # 可选，用于初次验证
```

---

## 4. 错误处理

| 场景 | HTTP Code | Detail |
|------|-----------|--------|
| 飞书签名验证失败 | 401 | "Invalid signature" |
| 飞书请求超时 | 502 | "Feishu API error" |
| JWT token无效 | 401 | "Not authenticated" |
| 任务不存在 | 404 | "Task not found" |
| 用户无权访问 | 403 | "Not authorized" |

---

## 5. 验收标准

- [ ] S9-F1: 飞书 Webhook 可接收消息，签名验证通过
- [ ] S9-F1: 可发送飞书卡片消息
- [ ] S9-F2: E2E测试脚本可运行，覆盖注册/登录/创建任务流程
- [ ] S9-F2: WebSocket连接测试通过
- [ ] S9-F2: 用户隔离验证通过
- [ ] S9-F3: 飞书消息触发Hermes任务创建
- [ ] S9-F4: WebSocket支持Authorization header
- [ ] S9-F4: 向后兼容query param方式
